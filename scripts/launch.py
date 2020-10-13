import sys
import tpDcc.loader

if __name__ == '__main__':
    for path in sys.path:
        print(path)

    tpDcc.loader.init(dev=False)
    tpDcc.ToolsMgr().launch_tool_by_id('tpDcc-tools-scripteditor', dev=True)