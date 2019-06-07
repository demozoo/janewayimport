import itertools

from django.core.management.base import BaseCommand
import MySQLdb

from janeway.models import Author, Membership, Name, Release, ReleaseType

PROD_TYPE_NAMES = {
    2: 'Diskmag',
    7: 'Musicdisk',
    9: 'Pack',
    11: 'Chip Music Pack',
    15: 'Cracktro',
    17: 'Cracktro',
    44: 'Demo',
    137: 'Demo',
    149: 'Diskmag',
    157: 'Intro',
    174: 'Demo',
    396: 'Slideshow',
    576: 'Tool',
    588: 'Tool',
    1680: 'Intro',
    1683: 'Demo',
    631: 'Docsdisk',
    795: 'Tool',
    796: 'Demo',
    797: 'Game',
    798: '40k Intro',
    799: 'Music',
    800: '4K Intro',
    801: '64K Intro',
    802: 'Pack',
    803: 'Video',
    804: 'Demo',
    805: ['Game', '32K Intro'],
    806: 'Intro',
    807: '1K Intro',
    808: 'Graphics',
    809: 'Intro',
    810: '16K Intro',
    811: 'Intro',
    812: 'Tool',
    813: 'Graphics',
    814: '96K Intro',
    815: '32K Intro',
    816: 'Intro',
    817: '2K Intro',
    818: '256b Intro',
    1632: 'Graphics',
    1536: 'Tool',
    1537: 'Tool',
    1630: 'Graphics',
    1639: 'Intro',
    1650: 'Demo',
    1852: 'Cracktro',
    1910: 'Executable Music',
    2113: 'ASCII',
    2206: 'Pack',
}


class Command(BaseCommand):
    def handle(self, **options):
        Name.objects.all().delete()
        Author.objects.all().delete()
        Membership.objects.all().delete()
        Release.objects.all().delete()

        mysql = MySQLdb.connect(user='janeway', db='janeway', passwd='janeway')

        c = mysql.cursor()

        # Import authors
        print("Importing authors")
        # AuthType: 0 = scener, 1 = group, 2 = BBS
        c.execute("""
            select AUTHORS.id as AuthorID, AuthType, NAMES.ID as NameID, Name, Abbrev, IsReal, Hidden
            from AUTHORS
            inner join NAMES on (AUTHORS.id = NAMES.AuthorID)
            where AuthType <> 2
            order by AUTHORS.id, NAMES.Secondary desc, NAMES.id
        """)

        author_id_map = {}
        name_id_map = {}
        primary_name_id_map = {}  # map janeway author ID to imported primary name ID
        release_map = {}

        for author_id, rows in itertools.groupby(c, lambda row: row[0]):
            rows = list(rows)
            is_group = (rows[0][1] == 1)

            real_name = ''
            real_name_hidden = False
            primary_name = None
            names = []

            for _, _, name_id, name, abbrev, is_real, hidden in rows:
                if not hidden and primary_name is None:
                    primary_name = name

                if is_real:
                    real_name = name
                    real_name_hidden = hidden

                if not hidden:
                    names.append(
                        (name_id, name, abbrev)
                    )

            if primary_name is None:
                raise Exception("No primary name for author %d" % author_id)

            author = Author.objects.create(
                janeway_id=author_id, name=primary_name, is_group=is_group,
                real_name=real_name, real_name_hidden=real_name_hidden
            )
            author_id_map[author_id] = author.id
            for name_id, name, abbrev in names:
                name_obj = author.names.create(
                    janeway_id=name_id, name=name, abbreviation=(abbrev or '')
                )
                name_id_map[name_id] = name_obj.id
                if name == primary_name:
                    primary_name_id_map[author_id] = name_obj.id

        # Import memberships
        print("Importing memberships")
        c.execute("""
            select AuthorID, GroupID, MEMBERS.Since, MEMBERS.Till, Founder
            from MEMBERS
            inner join AUTHORS as GROUPS on (GroupID = GROUPS.ID)
            inner join AUTHORS as MEMBERMEMBERS on (AuthorID = MEMBERMEMBERS.ID)
            where GROUPS.AuthType = 1  -- exclude BBSes
            and MEMBERMEMBERS.AuthType <> 2
        """)
        for member_id, group_id, since, until, founder in c:
            Membership.objects.create(
                member_id=author_id_map[member_id],
                group_id=author_id_map[group_id],
                since=since,
                until=until,
                founder=founder,
            )

        PRODUCTION_TYPES = [
            2, 7, 9, 11, 15, 17, 44, 137, 149, 157, 174, 396, 576, 588, 1680, 1683,
            631, 795, 796, 797, 798, 800, 801, 802, 803, 804, 805, 806, 807, 809, 810, 811, 812,
            814, 815, 816, 817, 818, 1636, 1536, 1537, 1639, 1650, 1852, 2206
        ]
        MUSIC_TYPES = [799, 1910]
        GRAPHICS_TYPES = [808, 813, 1630, 1632]

        # Import releases
        print("Importing releases")
        sql = """
            select ID, Title, TagID
            from RELEASES
            inner join RELEASE_COMMONS on (ReleaseID = ID)
            where TagID in (%(prodtype_ids)s)
        """ % {
            'prodtype_ids': ','.join([str(id) for id in PROD_TYPE_NAMES.keys()]),
        }
        c.execute(sql)

        for release_id, rows in itertools.groupby(c, lambda row: row[0]):
            rows = list(rows)
            title = rows[0][1]
            type_ids = set()
            type_names = set()
            for row in rows:
                type_id = row[2]
                type_ids.add(type_id)
                try:
                    type_name = PROD_TYPE_NAMES[type_id]
                    if isinstance(type_name, list):
                        for t in type_name:
                            type_names.add(t)
                    else:
                        type_names.add(type_name)
                except KeyError:
                    pass

            if any(type_id in PRODUCTION_TYPES for type_id in type_ids):
                supertype = 'production'
            elif any(type_id in MUSIC_TYPES for type_id in type_ids):
                supertype = 'music'
            elif any(type_id in GRAPHICS_TYPES for type_id in type_ids):
                supertype = 'graphics'
            else:
                continue

            release = Release.objects.create(
                janeway_id=release_id, title=title, supertype=supertype
            )
            release_map[release_id] = release
            for type_name in type_names:
                ReleaseType.objects.create(release=release, type_name=type_name)

        # Import credits / authors
        print("Importing credits / authors")
        c.execute("""
            select ID, ReleaseID, AuthorID, NameID, Job
            from CREDITS
            order by ReleaseID, Job
        """)
        for release_id, rows in itertools.groupby(c, lambda row: row[1]):
            rows = list(rows)
            has_overall_authors = rows[0][4] == 0  # use credits with job = 0 as authors

            try:
                release = release_map[release_id]
            except KeyError:
                continue  # this release was skipped (probably because it was an unwanted prod type)

            author_name_ids = set()

            for credit_id, _, author_id, name_id, job in rows:
                if has_overall_authors and job != 0:
                    continue

                if name_id is None or name_id == 0:
                    try:
                        author_name_ids.add(primary_name_id_map[author_id])
                    except KeyError:  # this author was skipped (probably because it was a BBS)
                        pass
                else:
                    try:
                        author_name_ids.add(name_id_map[name_id])
                    except KeyError:  # this name was skipped (probably because the author was a BBS)
                        pass

            for name_id in author_name_ids:
                release.author_names.add(name_id)
