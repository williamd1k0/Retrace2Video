
import sys
import os.path
import subprocess
from configparser import ConfigParser

if 'python.exe' in sys.executable:
    PATH = os.path.dirname(os.path.realpath(sys.argv[0]))
else:
    PATH = os.path.dirname(os.path.realpath(sys.executable))
VERSION = 1, 1, 0
APITRACE = 'apitrace.exe'
FFMPEG = 'ffmpeg.exe'
CONF = os.path.join(PATH, 'retrace2video.ini')
RAW_SFX = '-uncompressed'
SAMPLE_SFX = '-sample'
CREATE_NO_WINDOW = 0x08000000

UNCOMPRESSED = '"{0}" dump-images -o - "{1}" | "{2}" -r {3} -f image2pipe -vcodec ppm -i pipe: -r {3} -s {4} {5}'
COMPRESSED = '"{0}" dump-images -o - "{1}" | "{2}" -r {3} -f image2pipe -vcodec ppm -i pipe: {4}'

class Config(object):

    def __init__(self,
        output='output/', scale='1920x1080', fps=60, sample=True, apitrace='apitrace.exe',
        ffmpeg='ffmpeg.exe', rawcmd=None, samplecmd=None):

        self.output = path_from_relative(output)
        self.scale = scale
        self.fps = fps
        self.sample = sample
        self.apitrace = path_from_relative(os.path.join(apitrace, APITRACE))
        self.ffmpeg = path_from_relative(os.path.join(ffmpeg, FFMPEG))
        self.rawcmd = rawcmd
        self.samplecmd = samplecmd


def path_from_relative(path, full=PATH):
    if path[0:2] in ('.\\','./'):
        path = os.path.join(full, path[2:])
    return path


def dump_video(trace, configs):
    import re as regxp
    filename = regxp.sub('[\\\/]+', r'\\', trace).split('\\')[-1].replace('.trace', '')
    del regxp

    print(' Initializing: Configs')
    for key, value in configs.__dict__.items():
        print('  {}: {}'.format(key, value))

    print('\n Checking: output')
    recursive_mkdir(configs.output)

    print('\n Initializing: GL')
    print(' Initializing: FFMPEG')
    
    print('\n Warning: Do not resize the render window. It may interrupt the process!')

    print('\n Writing: uncompressed video')
    call_encoder(UNCOMPRESSED.format(
        configs.apitrace, trace, configs.ffmpeg, 
        configs.fps, configs.scale,
        configs.rawcmd.format(file=os.path.join(configs.output, filename+RAW_SFX))
    ), 'Error writing video')
    
    if configs.sample:
        print(' Writing: compressed sample')
        call_encoder(COMPRESSED.format(
            configs.apitrace, trace, configs.ffmpeg, configs.fps,
            configs.samplecmd.format(file=os.path.join(configs.output, filename+SAMPLE_SFX))
        ), 'Error writing sample')

    print('\n Done :)')


def call_encoder(command, err):
    import time, shlex
    process = subprocess.Popen(
        shlex.split(command), shell=True, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW
    )

    start = time.time()
    count = 1
    while process.poll() is None:
        print('%s%ds\r' % ('.'*count, time.time() - start), end='', flush=True)
        count += 1
        time.sleep(1)
    print('')

    if process.returncode != 0:
        print(err, file=sys.stderr)
        sys.exit(process.returncode)


def recursive_mkdir(path, start=''):
    if os.path.isdir(os.path.join(start, path)): return False
    import re as regxp
    paths = regxp.sub('[\\\/]+', r'\\', path).split('\\')
    paths_i = [start] if start != '' else []
    for folder in paths:
        paths_i.append(folder)
        absolute = '/'.join(paths_i)
        if not os.path.isdir(absolute):
            os.mkdir(absolute)
    del regxp


def create_config(conf):
    configs = ConfigParser()
    with open(conf, 'r', encoding='utf-8') as conf_file:
        try:
            configs.read_string(conf_file.read())
        except:
            print('  Error with config file!', file=sys.stderr)
            input()
    del conf_file

    dependencies = configs['DEPENDENCIES']
    general = configs['GENERAL']
    ffmpeg = configs['FFMPEG']

    return Config(
        general.get('output', './output'), general.get('scale', '1920x1080'),
        general.get('fps', '60'), general.getboolean('sample', True),
        dependencies.get('apitrace_path', './'), dependencies.get('ffmpeg_path', './'),
        ffmpeg.get('raw_cmd', '-vcodec libx264 -preset veryslow -qp 0 -y "{file}.mkv"'),
        ffmpeg.get('sample_cmd', '-vcodec mpeg4 -y "{file}.avi"')
    )


def write_config():
    config = ConfigParser()
    template = {
        "dependencies":{
            "apitrace_path": "./",
            "ffmpeg_path": "./"
        },
        "general": {
            "fps": "60",
            "scale": '1920x1080',
            "sample": 'yes',
            "output": "./output/"
        },
        "ffmpeg": {
            "raw_cmd": '-vcodec libx264 -preset veryslow -qp 0 -y "{file}.mkv"',
            "sample_cmd": '-vcodec mpeg4 -y "{file}.avi"'
        }
    }
    config['DEPENDENCIES'] = template['dependencies']
    config['GENERAL'] = template['general']
    config['FFMPEG'] = template['ffmpeg']

    with open(CONF, 'w', encoding='utf-8') as conf_w:
        config.write(conf_w)
    del conf_w
    print('First run: config file created!')
    input()
    sys.exit(0)


if __name__ == '__main__':

    print('Retrace 2 Video v{0}.{1}.{2} - ApiTrace Tool\n'.format(*VERSION))
    if not os.path.isfile(CONF): write_config()

    if len(sys.argv) <= 1:
        print('Don\'t open this executable, close it and drag the trace file over it or type via cli!', file=sys.stderr)
        input()
        sys.exit(1)
    elif not '.trace' in sys.argv[1]:
        print('Don\'t open this executable, close it and drag the trace file over it or type via cli!', file=sys.stderr)
        input()
        sys.exit(1)

    print(' Trace file: '+sys.argv[1].split('\\')[-1]+'\n')
    confs = create_config(CONF)
    dump_video(sys.argv[1], confs)

    input()