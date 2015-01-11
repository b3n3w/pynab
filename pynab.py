import config
import subprocess
import sys
import argparse

if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description="Pynab main scanning script")
    argparser.add_argument('start', action='store_true', help='update pynab')
    argparser.add_argument('update', action='store_true', help='update pynab')
    args = argparser.parse_args()

    if args.update:
        subprocess.call('git pull', shell=True)
        subprocess.call('alembic upgrade head', shell=True)
        subprocess.call('pip3 install -r requirements.txt', shell=True)
        print('pynab updated! if there were errors, you might need to re-run `pip3 install -r requirements.txt` with sudo.')
        sys.exit()

    elif args.start:
        if config.monitor.get('type') == 'teamocil':
            if not config.scan.get('pid_file') or not config.postprocess.get('pid_file') or not config.log.get('logging_file'):
                print('error: a pid_file or logging_file config option is not set in config.py')
                sys.exit()
            print('teamocil started')
        elif config.monitor.get('type') == 'screen':
            subprocess.call('screen -d -m -S start python3 start.py', shell=True)
            subprocess.cell('screen -d -m -S postprocess python3 postprocess.py', shell=True)
            print('Pynab started. If you\'re not using file logging, you can access the shells with screen -r start or screen -r postprocess.')
            sys.exit()
        elif config.monitor.get('type') == 'windows':
            subprocess.call('start python scan.py', shell=True)
            subprocess.call('start python postprocess.py', shell=True)
            subprocess.call('start python api.py', shell=True)
            print('Pynab started. You can use process manager to kill spawned processes (called python.exe).')
            print('Make sure that your PATH has python set to a python3 directory.')
            sys.exit()
        else:
            print('error: no monitor type set in config.py')
