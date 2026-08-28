param(
  [Parameter(Mandatory = $true)]
  [string]$RequestJson
)

$ErrorActionPreference = "Stop"

Add-Type -TypeDefinition @"
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Runtime.InteropServices;

public class CandidateResult
{
    public string address { get; set; }
    public string value { get; set; }
    public string type { get; set; }
}

public static class SoloForgeMemory
{
    private const int PROCESS_QUERY_INFORMATION = 0x0400;
    private const int PROCESS_VM_OPERATION = 0x0008;
    private const int PROCESS_VM_READ = 0x0010;
    private const int PROCESS_VM_WRITE = 0x0020;
    private const uint MEM_COMMIT = 0x1000;
    private const uint PAGE_GUARD = 0x100;
    private const uint PAGE_NOACCESS = 0x01;

    [StructLayout(LayoutKind.Sequential)]
    public struct MEMORY_BASIC_INFORMATION
    {
        public IntPtr BaseAddress;
        public IntPtr AllocationBase;
        public uint AllocationProtect;
        public IntPtr RegionSize;
        public uint State;
        public uint Protect;
        public uint Type;
    }

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr OpenProcess(int processAccess, bool bInheritHandle, int processId);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool CloseHandle(IntPtr hObject);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr VirtualQueryEx(IntPtr hProcess, IntPtr lpAddress, out MEMORY_BASIC_INFORMATION lpBuffer, IntPtr dwLength);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool ReadProcessMemory(IntPtr hProcess, IntPtr lpBaseAddress, byte[] lpBuffer, int dwSize, out IntPtr lpNumberOfBytesRead);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool WriteProcessMemory(IntPtr hProcess, IntPtr lpBaseAddress, byte[] lpBuffer, int nSize, out IntPtr lpNumberOfBytesWritten);

    private static ulong ToUInt64(IntPtr pointer)
    {
        return unchecked((ulong)pointer.ToInt64());
    }

    private static IntPtr ToIntPtr(ulong value)
    {
        return new IntPtr(unchecked((long)value));
    }

    private static bool IsReadable(uint protect)
    {
        if ((protect & PAGE_GUARD) != 0) return false;
        if ((protect & PAGE_NOACCESS) != 0) return false;
        return true;
    }

    private static byte[] BytesFor(string valueType, string rawValue)
    {
        string normalized = Convert.ToString(rawValue, CultureInfo.InvariantCulture);
        switch ((valueType ?? "").ToLowerInvariant())
        {
            case "int32":
                return BitConverter.GetBytes(Int32.Parse(normalized, CultureInfo.InvariantCulture));
            case "float":
                return BitConverter.GetBytes(Single.Parse(normalized, CultureInfo.InvariantCulture));
            case "double":
                return BitConverter.GetBytes(Double.Parse(normalized, CultureInfo.InvariantCulture));
            default:
                throw new ArgumentException("Unsupported value type: " + valueType);
        }
    }

    private static string DisplayValue(string valueType, string rawValue)
    {
        string normalized = Convert.ToString(rawValue, CultureInfo.InvariantCulture);
        switch ((valueType ?? "").ToLowerInvariant())
        {
            case "int32":
                return Int32.Parse(normalized, CultureInfo.InvariantCulture).ToString(CultureInfo.InvariantCulture);
            case "float":
                return Single.Parse(normalized, CultureInfo.InvariantCulture).ToString(CultureInfo.InvariantCulture);
            case "double":
                return Double.Parse(normalized, CultureInfo.InvariantCulture).ToString(CultureInfo.InvariantCulture);
            default:
                throw new ArgumentException("Unsupported value type: " + valueType);
        }
    }

    private static bool MatchesAt(byte[] buffer, int offset, byte[] needle)
    {
        for (int i = 0; i < needle.Length; i++)
        {
            if (buffer[offset + i] != needle[i]) return false;
        }
        return true;
    }

    private static ulong ParseAddress(string address)
    {
        string value = (address ?? "").Trim();
        if (value.StartsWith("0x", StringComparison.OrdinalIgnoreCase)) value = value.Substring(2);
        return UInt64.Parse(value, NumberStyles.HexNumber, CultureInfo.InvariantCulture);
    }

    private static CandidateResult Candidate(ulong address, string valueType, string value)
    {
        return new CandidateResult
        {
            address = "0x" + address.ToString("X", CultureInfo.InvariantCulture),
            value = DisplayValue(valueType, value),
            type = valueType
        };
    }

    public static CandidateResult[] FirstScan(int pid, string valueType, string rawValue, int limit, long maxBytes, int maxRegionBytes)
    {
        byte[] needle = BytesFor(valueType, rawValue);
        List<CandidateResult> candidates = new List<CandidateResult>();
        IntPtr handle = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, false, pid);
        if (handle == IntPtr.Zero) throw new InvalidOperationException("Could not open process for reading.");

        try
        {
            ulong address = 0x10000;
            ulong maxAddress = IntPtr.Size == 8 ? 0x00007FFFFFFEFFFFUL : 0x7FFF0000UL;
            long scanned = 0;
            int mbiSize = Marshal.SizeOf(typeof(MEMORY_BASIC_INFORMATION));

            while (address < maxAddress && candidates.Count < limit && scanned < maxBytes)
            {
                MEMORY_BASIC_INFORMATION info;
                IntPtr result = VirtualQueryEx(handle, ToIntPtr(address), out info, new IntPtr(mbiSize));
                if (result == IntPtr.Zero)
                {
                    address += 0x10000;
                    continue;
                }

                ulong baseAddress = ToUInt64(info.BaseAddress);
                ulong regionSize = ToUInt64(info.RegionSize);
                if (regionSize == 0) break;

                if (info.State == MEM_COMMIT && IsReadable(info.Protect))
                {
                    int toRead = (int)Math.Min(regionSize, (ulong)Math.Min(maxRegionBytes, Math.Max(0, maxBytes - scanned)));
                    if (toRead >= needle.Length)
                    {
                        byte[] buffer = new byte[toRead];
                        IntPtr bytesRead;
                        if (ReadProcessMemory(handle, ToIntPtr(baseAddress), buffer, toRead, out bytesRead))
                        {
                            int count = Math.Max(0, bytesRead.ToInt32());
                            scanned += count;
                            for (int i = 0; i <= count - needle.Length && candidates.Count < limit; i++)
                            {
                                if (MatchesAt(buffer, i, needle))
                                {
                                    candidates.Add(Candidate(baseAddress + (ulong)i, valueType, rawValue));
                                }
                            }
                        }
                    }
                }

                ulong next = baseAddress + regionSize;
                if (next <= address) next = address + 0x10000;
                address = next;
            }
        }
        finally
        {
            CloseHandle(handle);
        }

        return candidates.ToArray();
    }

    public static CandidateResult[] NarrowScan(int pid, string valueType, string rawValue, string[] addresses)
    {
        byte[] needle = BytesFor(valueType, rawValue);
        List<CandidateResult> matches = new List<CandidateResult>();
        IntPtr handle = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, false, pid);
        if (handle == IntPtr.Zero) throw new InvalidOperationException("Could not open process for reading.");

        try
        {
            foreach (string addressText in addresses)
            {
                ulong address = ParseAddress(addressText);
                byte[] buffer = new byte[needle.Length];
                IntPtr bytesRead;
                if (ReadProcessMemory(handle, ToIntPtr(address), buffer, buffer.Length, out bytesRead) && bytesRead.ToInt32() == needle.Length)
                {
                    if (MatchesAt(buffer, 0, needle)) matches.Add(Candidate(address, valueType, rawValue));
                }
            }
        }
        finally
        {
            CloseHandle(handle);
        }

        return matches.ToArray();
    }

    public static bool WriteValue(int pid, string addressText, string valueType, string rawValue)
    {
        byte[] value = BytesFor(valueType, rawValue);
        ulong address = ParseAddress(addressText);
        IntPtr handle = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ | PROCESS_VM_OPERATION | PROCESS_VM_WRITE, false, pid);
        if (handle == IntPtr.Zero) throw new InvalidOperationException("Could not open process for writing.");

        try
        {
            IntPtr written;
            return WriteProcessMemory(handle, ToIntPtr(address), value, value.Length, out written) && written.ToInt32() == value.Length;
        }
        finally
        {
            CloseHandle(handle);
        }
    }
}
"@

function Write-JsonResponse($Value) {
  $Value | ConvertTo-Json -Depth 8 -Compress
}

try {
  $request = $RequestJson | ConvertFrom-Json

  switch ($request.action) {
    "listProcesses" {
      $currentPid = $PID
      $processes = Get-Process | ForEach-Object {
        $path = $null
        try { $path = $_.Path } catch { $path = $null }
        [pscustomobject]@{
          pid = $_.Id
          name = $_.ProcessName
          title = $_.MainWindowTitle
          path = $path
        }
      } | Where-Object {
        $_.pid -ne $currentPid -and $_.name
      } | Sort-Object name, pid

      Write-JsonResponse ([pscustomobject]@{
        ok = $true
        available = $true
        processes = @($processes)
      })
    }
    "firstScan" {
      $candidates = [SoloForgeMemory]::FirstScan(
        [int]$request.pid,
        [string]$request.valueType,
        [string]$request.value,
        [int]$request.candidateLimit,
        [long]$request.maxBytes,
        [int]$request.maxRegionBytes
      )
      Write-JsonResponse ([pscustomobject]@{
        ok = $true
        available = $true
        candidates = @($candidates)
      })
    }
    "narrowScan" {
      $addresses = @($request.addresses | ForEach-Object { [string]$_ })
      $candidates = [SoloForgeMemory]::NarrowScan(
        [int]$request.pid,
        [string]$request.valueType,
        [string]$request.value,
        [string[]]$addresses
      )
      Write-JsonResponse ([pscustomobject]@{
        ok = $true
        available = $true
        candidates = @($candidates)
      })
    }
    "writeValue" {
      $written = [SoloForgeMemory]::WriteValue(
        [int]$request.pid,
        [string]$request.address,
        [string]$request.valueType,
        [string]$request.value
      )
      Write-JsonResponse ([pscustomobject]@{
        ok = $written
        available = $true
        written = $written
        address = [string]$request.address
      })
    }
    default {
      throw "Unsupported action: $($request.action)"
    }
  }
} catch {
  Write-JsonResponse ([pscustomobject]@{
    ok = $false
    error = $_.Exception.Message
  })
  exit 1
}
