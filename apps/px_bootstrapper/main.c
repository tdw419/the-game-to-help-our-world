#include <UIKit/UIKit.h>

unsigned char px_runtime_ztxt[] = { /* incbin pxruntime.ztxt.bin */ };
unsigned char px_boot_ztxt[] = { /* incbin pxboot.ztxt.bin */ };
unsigned char px_upgrade_pxexe[] = { /* incbin PX_UPGRADE.pxexe.bin */ };
unsigned char px_executor_pxmod[] = { /* incbin pxexecutor.pxmod.bin */ };
unsigned char px_canvas_ztxt[] = { /* incbin pxcanvas.ztxt.bin */ };
unsigned char px_os_io_ztxt[] = { /* incbin pxos_io.ztxt.bin */ };
unsigned char pxos_config_json[] = { /* incbin PXOS.config.json.bin */ };
unsigned char pxvm_font_png[] = { /* incbin pxvm_font.png.bin */ };

unsigned int pixel_grid[1024*768];
char log_buffer[1024];
char digest_buffer[4096];
unsigned long registers[4];
unsigned long pc = 0;
char running = 1;

void execute_ztxt(unsigned char* ztxt) {
    while (running && *ztxt) {
        if (*ztxt == 'M' && strncmp(ztxt, "MOV ", 4) == 0) {
            registers[0] = registers[1];
            ztxt += 8;
        } else if (*ztxt == 'S' && strncmp(ztxt, "SET_PX", 6) == 0) {
            unsigned int x = registers[0], y = registers[1];
            pixel_grid[x*1024 + y] = 0xFF0000FF;
            ztxt += 12;
        } else if (*ztxt == 'P' && strncmp(ztxt, "PX_WRITE", 8) == 0) {
            log_buffer[0] = 'W';
            ztxt += 20;
        } else if (*ztxt == 'P' && strncmp(ztxt, "PX_RELOAD", 9) == 0) {
            execute_ztxt(px_executor_pxmod);
            ztxt += 15;
        } else if (*ztxt == 'P' && strncmp(ztxt, "PX_EXEC", 7) == 0) {
            execute_ztxt(px_upgrade_pxexe);
            ztxt += 15;
        } else if (*ztxt == 'P' && strncmp(ztxt, "PX_EXPORT", 9) == 0) {
            NSString* path = @"PXOS_reflex_digest.json";
            [@{@"pxmodules": @{@"pxexecutor.pxmod": @"tick: LOG 'PXRuntime Upgraded'",
                               @"PX_UPGRADE_LOG.zTXT": @"pxexecutor updated"},
               @"status": @"PXSELFEDIT COMPLETE"} writeToFile:path atomically:YES];
            ztxt += 15;
        } else if (*ztxt == 'L' && strncmp(ztxt, "LOG ", 4) == 0) {
            log_buffer[1] = 'L';
            ztxt += 10;
        } else if (*ztxt == 'H' && strncmp(ztxt, "HLT", 3) == 0) {
            running = 0;
            ztxt += 4;
        }
        pc++;
        ztxt++;
    }

    NSString* log_path = @"pxos_log.txt";
    [[NSString stringWithUTF8String:log_buffer] writeToFile:log_path atomically:YES];
}

@interface PXView : UIView
@end

@implementation PXView
- (void)drawRect:(CGRect)rect {
    CGContextRef ctx = UIGraphicsGetCurrentContext();
    CGContextSetRGBFillColor(ctx, 0, 0, 0, 1);
    CGContextFillRect(ctx, rect);
    CGContextSetRGBFillColor(ctx, 1, 0, 0, 1);
    CGContextFillRect(ctx, CGRectMake(0, 0, 1, 1));
}
@end

@interface AppDelegate : UIResponder <UIApplicationDelegate>
@property (strong, nonatomic) UIWindow *window;
@end

@implementation AppDelegate
- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {
    self.window = [[UIWindow alloc] initWithFrame:[[UIScreen mainScreen] bounds]];
    self.window.rootViewController = [[UIViewController alloc] init];
    self.window.rootViewController.view = [[PXView alloc] initWithFrame:self.window.bounds];
    [self.window makeKeyAndVisible];
    execute_ztxt(px_runtime_ztxt);
    return YES;
}
@end

int main(int argc, char *argv[]) {
    @autoreleasepool {
        return UIApplicationMain(argc, argv, nil, NSStringFromClass([AppDelegate class]));
    }
}