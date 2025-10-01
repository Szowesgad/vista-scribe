from setuptools import setup

# py2app options
OPTIONS = {
    # don't emulate command-line arguments
    "argv_emulation": False,
    # required plist entries
    "plist": {
        # makes it a background app (no dock icon)
        "LSUIElement": True,
        # display name
        "CFBundleName": "vista-scribe",
        # description shown when asking for mic permission
        "NSMicrophoneUsageDescription": "Needed to transcribe speech.",
        # add info about accessibility usage for clarity
        "NSAccessibilityUsageDescription": "Needed to simulate paste (Cmd+V) and monitor hotkeys.",
        # note: nssystemadministrationrequiresauthenticationset is not needed unless modifying system files
    },
    # potentially exclude unnecessary large packages if needed later
    # 'packages': ['rumps', 'etc'],
    # 'excludes': ['tkinter', 'unittest'],
}

# setup configuration
setup(
    # main application script
    app=["../main.py"],  # path relative to this setup.py file
    # py2app specific options
    options={"py2app": OPTIONS},
    # dependency needed to run setup.py itself
    setup_requires=["py2app"],
    name="vista-scribe",  # name for the build process
)
