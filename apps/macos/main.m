#import <Cocoa/Cocoa.h>
#import <WebKit/WebKit.h>

@interface SoloForgeBridge : NSObject <WKScriptMessageHandler>
@property(nonatomic, weak) WKWebView *webView;
@property(nonatomic, strong) NSURL *resourceURL;
- (instancetype)initWithWebView:(WKWebView *)webView resourceURL:(NSURL *)resourceURL;
@end

@implementation SoloForgeBridge

- (instancetype)initWithWebView:(WKWebView *)webView resourceURL:(NSURL *)resourceURL {
    self = [super init];
    if (self) {
        _webView = webView;
        _resourceURL = resourceURL;
    }
    return self;
}

- (void)userContentController:(WKUserContentController *)userContentController didReceiveScriptMessage:(WKScriptMessage *)message {
    if (![message.name isEqualToString:@"soloforge"] || ![message.body isKindOfClass:[NSDictionary class]]) {
        return;
    }
    NSDictionary *payload = (NSDictionary *)message.body;
    if ([payload[@"type"] isEqualToString:@"scanInstalledGames"]) {
        [self scanInstalledGames];
    }
}

- (void)scanInstalledGames {
    NSURL *scannerURL = [self.resourceURL URLByAppendingPathComponent:@"tools/scan_installed_games.py"];
    NSTask *task = [[NSTask alloc] init];
    task.executableURL = [NSURL fileURLWithPath:@"/usr/bin/python3"];
    task.arguments = @[scannerURL.path, @"--all-drives", @"--pretty"];
    task.currentDirectoryURL = self.resourceURL;

    NSPipe *stdoutPipe = [NSPipe pipe];
    NSPipe *stderrPipe = [NSPipe pipe];
    task.standardOutput = stdoutPipe;
    task.standardError = stderrPipe;

    __weak typeof(self) weakSelf = self;
    task.terminationHandler = ^(NSTask *finishedTask) {
        NSData *stdoutData = [[stdoutPipe fileHandleForReading] readDataToEndOfFile];
        NSData *stderrData = [[stderrPipe fileHandleForReading] readDataToEndOfFile];
        NSString *stdoutText = [[NSString alloc] initWithData:stdoutData encoding:NSUTF8StringEncoding] ?: @"";
        NSString *stderrText = [[NSString alloc] initWithData:stderrData encoding:NSUTF8StringEncoding] ?: @"";

        if (finishedTask.terminationStatus == 0) {
            [weakSelf dispatchScanResult:stdoutText];
        } else {
            NSString *message = stderrText.length ? stderrText : [NSString stringWithFormat:@"Scanner exited with status %d", finishedTask.terminationStatus];
            [weakSelf dispatchScanError:message];
        }
    };

    NSError *error = nil;
    if (![task launchAndReturnError:&error]) {
        [self dispatchScanError:[NSString stringWithFormat:@"Could not start scanner: %@", error.localizedDescription]];
    }
}

- (NSString *)jsonStringLiteral:(NSString *)value {
    NSData *data = [NSJSONSerialization dataWithJSONObject:@[value ?: @""] options:0 error:nil];
    NSString *arrayJSON = [[NSString alloc] initWithData:data encoding:NSUTF8StringEncoding] ?: @"[\"\"]";
    return [arrayJSON substringWithRange:NSMakeRange(1, arrayJSON.length - 2)];
}

- (void)dispatchScanResult:(NSString *)json {
    NSString *script = [NSString stringWithFormat:
        @"window.dispatchEvent(new CustomEvent('soloforge-native-scan', { detail: { ok: true, payload: %@ } }));",
        json.length ? json : @"{}"];
    dispatch_async(dispatch_get_main_queue(), ^{
        [self.webView evaluateJavaScript:script completionHandler:nil];
    });
}

- (void)dispatchScanError:(NSString *)message {
    NSString *escaped = [self jsonStringLiteral:message];
    NSString *script = [NSString stringWithFormat:
        @"window.dispatchEvent(new CustomEvent('soloforge-native-scan', { detail: { ok: false, error: %@ } }));",
        escaped];
    dispatch_async(dispatch_get_main_queue(), ^{
        [self.webView evaluateJavaScript:script completionHandler:nil];
    });
}

@end

@interface AppDelegate : NSObject <NSApplicationDelegate>
@property(nonatomic, strong) NSWindow *window;
@property(nonatomic, strong) SoloForgeBridge *bridge;
@end

@implementation AppDelegate

- (void)applicationDidFinishLaunching:(NSNotification *)notification {
    NSURL *resourceURL = NSBundle.mainBundle.resourceURL;
    if (!resourceURL) {
        [NSApp terminate:nil];
        return;
    }

    WKWebViewConfiguration *configuration = [[WKWebViewConfiguration alloc] init];
    WKUserContentController *userContentController = [[WKUserContentController alloc] init];
    configuration.userContentController = userContentController;

    WKWebView *webView = [[WKWebView alloc] initWithFrame:NSZeroRect configuration:configuration];
    self.bridge = [[SoloForgeBridge alloc] initWithWebView:webView resourceURL:resourceURL];
    [userContentController addScriptMessageHandler:self.bridge name:@"soloforge"];

    self.window = [[NSWindow alloc]
        initWithContentRect:NSMakeRect(0, 0, 1280, 820)
                  styleMask:(NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskMiniaturizable | NSWindowStyleMaskResizable)
                    backing:NSBackingStoreBuffered
                      defer:NO];
    self.window.title = @"SoloForge";
    self.window.contentView = webView;
    [self.window center];
    [self.window makeKeyAndOrderFront:nil];

    NSURL *appURL = [resourceURL URLByAppendingPathComponent:@"desktop/index.html"];
    [webView loadFileURL:appURL allowingReadAccessToURL:resourceURL];
}

- (BOOL)applicationShouldTerminateAfterLastWindowClosed:(NSApplication *)sender {
    return YES;
}

@end

int main(int argc, const char *argv[]) {
    @autoreleasepool {
        NSApplication *app = [NSApplication sharedApplication];
        AppDelegate *delegate = [[AppDelegate alloc] init];
        app.delegate = delegate;
        [app setActivationPolicy:NSApplicationActivationPolicyRegular];
        [app activateIgnoringOtherApps:YES];
        [app run];
    }
    return 0;
}
