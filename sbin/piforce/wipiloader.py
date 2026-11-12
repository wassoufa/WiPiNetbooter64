import os, collections, signal, sys, subprocess, socket, logging
import psutil
import RPi.GPIO as GPIO
import glob
import csv
from time import sleep
sys.path.append('/sbin/piforce/dm_netboot/netdimm/')
from netdimm import NetDimm
from upload_status import UploadStatus, UploadBusy, sender_error

def checkprocess(process):
    for proc in psutil.process_iter():
        try:
            if process.lower() in proc.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def exists(path):
    try:
        os.stat(path)
    except OSError:
        return False
    return True

def main():
    activedimm = sys.argv[2]
    with open('/sbin/piforce/servermode.txt') as srvfile:
        srvmode = srvfile.readline()

    job = None
    # Server Mode retains its persistent sender/replacement lifecycle.
    if srvmode != 'serveron':
        try:
            job = UploadStatus(activedimm, sys.argv[1])
        except UploadBusy:
            logging.basicConfig(filename="/var/log/wipiloader.log", format='%(asctime)s %(message)s', filemode='a', level=logging.WARNING)
            logging.warning("Launch ignored: upload already in progress for %s", activedimm)
            return 0

    try:
        logging.basicConfig(filename="/var/log/wipiloader.log", format='%(asctime)s %(message)s', filemode='w')
        logger=logging.getLogger()
        logger.setLevel(logging.DEBUG)
        sys.stderr.write = logger.error
        sys.stdout.write = logger.info

        with open('/sbin/piforce/openmode.txt') as openjvsfile:
            openjvs = openjvsfile.readline()
        with open('/sbin/piforce/ffbmode.txt') as ffbfile:
            ffbmode = ffbfile.readline()
        with open('/sbin/piforce/emumode.txt') as emufile:
            emumode = emufile.readline()
        with open('/sbin/piforce/hatserial.txt') as hatfile:
            hatserial = hatfile.readline()

        with open('/sbin/piforce/rpiversion.txt') as rpiversionfile:
            rpiversion = rpiversionfile.readline()

        print("Wipiloader script started")
        print("OpenJVS mode is", openjvs)
        print("OpenFFB mode is", ffbmode)
        print("Card emulator mode is", emumode)
        print("Server mode is", srvmode)
        print("Active dimm is", activedimm)

        if (openjvs == 'openon'):
            dimmdict = {}
            with open('/var/www/html/csv/dimms.csv', newline='') as csvfile:
                filereader = csv.reader(csvfile, delimiter=',')
                for row in filereader:
                    dimmdict[row[1]] = row[3]
            if (dimmdict[activedimm] == 'on'):
                openjvsCommand1 = 'sudo killall -9 openjvs > /var/log/openjvs/openjvs.log 2>&1'
                os.system(openjvsCommand1)
                print("Starting OpenJVS with mapping file", sys.argv[5])
                openjvsCommand2 = 'sudo openjvs '+sys.argv[5]+' >> /var/log/openjvs/openjvs.log 2>&1 &'
                os.system(openjvsCommand2)

        if (ffbmode == 'ffbon'):
            ffbCommand1 = 'sudo killall -9 openffb > /var/log/openffb/openffb.log 2>&1'
            os.system(ffbCommand1)
            sleep(5);
            print("Starting OpenFFB with mapping file", sys.argv[6])
            ffbCommand2 = 'sudo openffb -h=0 -gp='+sys.argv[6]+' >> /var/log/openffb/openffb.log 2>&1 &'
            os.system(ffbCommand2)

        activeromCommand = 'sudo echo -n '+sys.argv[2]+' | tee /var/log/activerom/'+sys.argv[1]
        os.system(activeromCommand)
        logCommand = 'sudo echo -n '+sys.argv[1]+' '+sys.argv[2]+' | tee /var/www/logs/log.txt'
        os.system(logCommand)

        print()

        rom_dir = '/boot/roms/'
        romfile = rom_dir+sys.argv[1]

        print("Requested rom file is", romfile)

        if (emumode == 'auto'):
            if exists('/dev/COM1'):
                compath = '/dev/'+os.readlink('/dev/COM1')
                devices = glob.glob('/dev/ttyUSB*')
                for device in devices:
                    if (device != compath):
                        emuport = device
                        break
            else:
                emuport = '/dev/ttyUSB0'
            if (hatserial == 'hatserialon'):
                if ('5' in rpiversion):
                    emuport = '/dev/ttyAMA3'
                elif ('4' in rpiversion):
                    emuport = '/dev/ttyAMA4'
                else:
                    emuport = '/dev/ttyUSB0'

            if ('initial_d' in romfile):
                if ('initial_d_3' in romfile):
                    IDMode = 'id3'
                elif ('initial_d_2' in romfile):
                    IDMode = 'id2'
                else:
                    IDMode = 'idas'
                emuCommand = 'sudo python3 /sbin/piforce/card_emulator/idcardemu.py -cp '+emuport+' -m '+IDMode+' &'
                os.system(emuCommand)

            if ('fzeroax_SBGG' in romfile):
                emuCommand = 'sudo python3 /sbin/piforce/card_emulator/fzerocardemu.py -cp '+emuport+' &'
                os.system(emuCommand)

            if ('mariokartarcadegp_SBKP' in romfile):
                emuCommand = 'sudo python3 /sbin/piforce/card_emulator/mkgpcardemu.py -cp '+emuport+' -m mkgp &'
                os.system(emuCommand)

            if ('mariokartarcadegp2_SBNL' in romfile):
                emuCommand = 'sudo python3 /sbin/piforce/card_emulator/mkgpcardemu.py -cp '+emuport+' -m mkgp2 &'
                os.system(emuCommand)

            if ('SBHQ' in romfile):
                emuCommand = 'sudo python3 /sbin/piforce/card_emulator/wmmtcardemu.py -cp '+emuport+' -m wmmt &'
                os.system(emuCommand)

            if ('SBKD' in romfile):
                emuCommand = 'sudo python3 /sbin/piforce/card_emulator/wmmtcardemu.py -cp '+emuport+' -m wmmt2 &'
                os.system(emuCommand)

        if ('monster_ride' in romfile or 'cycraft' in romfile):
            cycraftCommand = 'sudo /usr/lib/cycraft &'
            os.system(cycraftCommand)

        if ('mariokartarcadegp' in romfile and exists('/dev/video0')):
            camCommand = 'sudo /usr/local/bin/mjpg_streamer -i "input_uvc.so -r 320x240 -d /dev/video0 -f 30" -o "output_http.so -p 8080 -w /usr/local/share/mjpg-streamer/www" &'
            os.system(camCommand)

        if (srvmode == 'serveron'):
            print("Server mode is on - starting netdimm_ensure script")
            loaderCommand = 'sudo python3 /sbin/piforce/dm_netboot/netdimm_ensure '+activedimm+' '+romfile
            os.system(loaderCommand)
        else:
            print("Server mode is off - starting netdimm_send script")
            result = subprocess.run(
                ['sudo', 'python3', '/sbin/piforce/dm_netboot/netdimm_send', activedimm, romfile, '--disable-crc'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            if result.returncode != 0:
                job.finish(False, sender_error(result, activedimm, sys.argv[1]))
                return 1
            job.finish(True)

        if sys.argv[4] == 'hackon':
            print("Time Hack mode is on - starting timehack script")
            hackCommand = 'sudo python3 /sbin/piforce/timehack.py '+activedimm+' &'
            os.system(hackCommand)

        return 0

    except Exception as error:
        logging.exception("Game loading failed")
        if job is not None and job.state['state'] == 'active':
            job.finish(False, str(error))
        return 1
    finally:
        if job is not None:
            job.close()


if __name__ == '__main__':
    sys.exit(main())
