import re
from urllib.parse import quote


def expand(path, file_type):
    path = path.strip()

    # return full URLs immediately
    if path.startswith('http:') or path.startswith('ftp:'):
        return path

    # strip leading slash
    if path.startswith('/'):
        path = path[1:]

    if path == 'Roland/b universe.mo':
        return 'http://modland.com/pub/modules/Protracker/Roland/b%20universe.mod'

    if path == 'SDH/cp-songen!!.mod':
        return 'http://modland.com/pub/modules/Protracker/SDH/cp-songen!!.mod'

    if path == 'Roberts/relax with em-05.mod':
        return 'http://modland.com/pub/modules/Protracker/Roberts/relax%20with%20em-05.mod'

    if path == 'Flovius/scared - main.mod':
        return 'http://modland.com/pub/modules/Protracker/Flovius/scared%20-%20main.mod'

    if path == 'T/T-Various/TheCrackingCompany-3rd.lha':
        return 'http://ftp.amigascne.org/pub/amiga/Groups/T/T-Various/TheCrackingCompany-3rd.lha'

    if path == 'pub/amiga/Groups/C/CarillonCyberiad/Cyberiad-MorbidVisions1Bfix.dms':
        return 'http://ftp.amigascne.org/pub/amiga/Groups/C/CarillonCyberiad/Cyberiad-MorbidVisions1Bfix.dms'

    if path == 'MOD.Chypnotize!.gz':
        return 'https://files.scene.org/get/parties/2017/revision17/oldskool_music/dascon-chypnotize.zip'

    root = path.split('/')[0]

    if root in ('Groups', 'Docdisks', 'Packdisks', 'Parties', 'PartyInvites', 'Tools', 'Sound', 'UtilityDisks', 'Trackerpacker'):
        return 'http://ftp.amigascne.org/pub/amiga/' + quote(path)

    if root == 'modules':
        return 'http://amp.dascene.net/' + quote(path)

    if root in (
        'The Musical Enlightenment', 'Protracker', 'Delta Music 2', 'Ron Klaren', 'Soundtracker',
        'Future Composer 1.4', 'SidMon 1', 'Music Assembler', 'Hippel COSO', 'Digibooster',
        'Digibooster Pro', 'AHX', 'Startrekker AM', 'BP SoundMon 2', 'OctaMED MMD1',
        'JamCracker', 'Future Composer 1.3', 'Sonic Arranger', 'Digital Mugician', 'Speedy System',
        'Hippel', 'Game Music Creator', 'Maniacs Of Noise', 'HivelyTracker', 'SoundFX', 'Delta Music',
        'Delitracker Custom', 'OctaMED MMD0', 'SidMon 2', 'Art Of Noise', 'Mark II', 'Jason Brooke'
    ):
        return 'http://modland.com/pub/modules/' + quote(path)

    if (len(root) == 1 or root == 'UnknownArtist' or root == 'Unknown') and file_type == 4:  # graphics
        return 'http://ftp.amigascne.org/pub/amiga/Gfx/' + quote(path)

    if root == 'Modules' and file_type == 1:
        path = re.sub('^Modules', 'modules', path)
        return 'http://amp.dascene.net/' + quote(path)

    if root == 'Pearl':
        return 'http://ftp.amigascne.org/pub/amiga/Groups/P/' + quote(path)

    if root == 'DarryBooper':
        return 'http://ftp.amigascne.org/pub/amiga/Packdisks/' + quote(path)

    if root == 'NoGroup':
        return 'http://ftp.amigascne.org/pub/amiga/Groups/' + quote(path)

    if root == 'Hippel-COSO':
        path = re.sub('^Hippel-COSO', 'Hippel COSO', path)
        return 'http://modland.com/pub/modules/' + quote(path)

    raise ValueError("Unrecognised URL path: %s" % path)
