// Press a macOS virtual key for a timed hold (emulator input tests). Usage: hold-key <keycode> <seconds>
import Foundation
import CoreGraphics
let code = CGKeyCode(Int(CommandLine.arguments[1])!)
let hold = Double(CommandLine.arguments[2])!
let src = CGEventSource(stateID: .hidSystemState)
CGEvent(keyboardEventSource: src, virtualKey: code, keyDown: true)!.post(tap: .cghidEventTap)
Thread.sleep(forTimeInterval: hold)
CGEvent(keyboardEventSource: src, virtualKey: code, keyDown: false)!.post(tap: .cghidEventTap)
