import datetime
import itertools

from django.core.management.base import BaseCommand
import MySQLdb

from janeway.links import expand
from janeway.models import Author, Credit, DownloadLink, Membership, Name, PackContent, Release, ReleaseType, SoundtrackLink

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
    1910: 'Intro',
    2113: 'ASCII',
    2206: 'Pack',
}

JOBS = {
    0: ('Other', None),
    1: ('Code', None),
    2: ('Music', None),
    3: ('Graphics', None),
    4: ('Text', None),
    5: ('Text', 'Editing'),
    6: ('Code', 'Crack'),
    7: ('Code', 'Trainer'),
    8: ('Other', 'Supply'),
    9: ('Graphics', 'Design'),
    10: ('Code', 'Fix'),
    11: ('Other', 'Moral support'),
    12: ('Graphics', 'ASCII art'),
    13: ('Graphics', '.diz file logo'),
}


class Command(BaseCommand):
    def handle(self, **options):
        Name.objects.all().delete()
        Author.objects.all().delete()
        Membership.objects.all().delete()
        Release.objects.all().delete()
        PackContent.objects.all().delete()
        Credit.objects.all().delete()
        DownloadLink.objects.all().delete()
        SoundtrackLink.objects.all().delete()

        mysql = MySQLdb.connect(user='janeway', db='janeway', passwd='janeway')

        c = mysql.cursor()

        # Import authors
        print("Importing authors")
        # AuthType: 0 = scener, 1 = group, 2 = BBS
        c.execute("""
            select
                AUTHORS.id as AuthorID, AuthType, COUNTRIES.Code,
                case when COMPANY_TAG.TagID is null then 0 else 1 end as IsCompany,
                NAMES.ID as NameID, NAMES.Name, Abbrev, IsReal, Hidden
            from AUTHORS
            inner join NAMES on (AUTHORS.id = NAMES.AuthorID)
            left join COUNTRIES on (AUTHORS.CountryID = COUNTRIES.ID)
            left join AUTHOR_COMMONS as COMPANY_TAG on (AUTHORS.id = COMPANY_TAG.AuthorID and COMPANY_TAG.TagID = 1641)
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
            country_code = (rows[0][2] or '').upper()
            if country_code == 'WORLDWIDE':
                country_code = ''
            is_company = bool(rows[0][3])

            real_name = ''
            real_name_hidden = False
            primary_name = None
            names = []

            for _, _, _, _, name_id, name, abbrev, is_real, hidden in rows:
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
                real_name=real_name, real_name_hidden=real_name_hidden,
                country_code=country_code, is_company=is_company
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
            814, 815, 816, 817, 818, 1636, 1536, 1537, 1639, 1650, 1852, 1910, 2206
        ]
        MUSIC_TYPES = [799]
        GRAPHICS_TYPES = [808, 813, 1630, 1632]

        # Import releases
        print("Importing releases")
        sql = """
            select ID, Title, TagID, cast(Date as char) as ReleaseDate
            from RELEASES
            inner join RELEASE_COMMONS on (ReleaseID = ID)
            where TagID in (%(prodtype_ids)s)
            and ID not in (select ReleaseID from RELEASE_COMMONS where TagID = 797) -- skip 'originals'
            and ID not in (select FeatureID from FEATURES where FeatureType in (2, 3)) -- skip demopack intros and megademo parts
        """ % {
            'prodtype_ids': ','.join([str(id) for id in PROD_TYPE_NAMES.keys()]),
        }
        c.execute(sql)

        for release_id, rows in itertools.groupby(c, lambda row: row[0]):
            rows = list(rows)
            title = rows[0][1]
            release_date_string = rows[0][3]

            if (not release_date_string) or release_date_string[0:4] == '0000':
                release_date = None
                release_date_precision = ''
            elif release_date_string[5:7] == ('00'):
                release_date = datetime.date(int(release_date_string[0:4]), 1, 1)
                release_date_precision = 'y'
            elif release_date_string[8:10] == ('00'):
                release_date = datetime.date(int(release_date_string[0:4]), int(release_date_string[5:7]), 1)
                release_date_precision = 'm'
            else:
                release_date = datetime.date(int(release_date_string[0:4]), int(release_date_string[5:7]), int(release_date_string[8:10]))
                release_date_precision = 'd'

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
                janeway_id=release_id, title=title, supertype=supertype,
                release_date_date=release_date, release_date_precision=release_date_precision
            )
            release_map[release_id] = release
            for type_name in type_names:
                ReleaseType.objects.create(release=release, type_name=type_name)

        print("Setting release platforms")

        # PPC entries
        c.execute("""
            select ReleaseID from RELEASE_COMMONS
            where TagID in (2006, 2152)
        """)
        ppc_release_ids = [row[0] for row in c]
        Release.objects.filter(janeway_id__in=ppc_release_ids).update(platform='ppc')

        # AGA entries
        c.execute("""
            select ReleaseID from RELEASE_COMMONS
            where TagID = 794
        """)
        aga_release_ids = [row[0] for row in c]
        Release.objects.filter(janeway_id__in=aga_release_ids).update(platform='aga')

        # OCS/ECS
        Release.objects.filter(platform='').update(platform='ocs')

        # Import pack contents
        print("Importing pack contents")
        c.execute("""
            select ReleaseID, FeatureID
            from FEATURES
            where FeatureType = 1
        """)
        for pack_id, content_id in c:
            try:
                pack = release_map[pack_id]
            except KeyError:
                continue  # this release was skipped (probably because it was an unwanted prod type)
            try:
                content = release_map[content_id]
            except KeyError:
                continue  # this release was skipped (probably because it was an unwanted prod type)

            PackContent.objects.create(pack=pack, content=content)

        print("Setting aliases for pack intros / demo parts")
        c.execute("""
            select ReleaseID, FeatureID
            from FEATURES
            where FeatureType in (2, 3)
        """)
        for release_id, part_id in c:
            try:
                release = release_map[release_id]
            except KeyError:
                continue

            release_map[part_id] = release

        # Import credits / authors
        print("Importing credits / authors")
        c.execute("""
            select ID, ReleaseID, AuthorID, NameID, Job, CustomJob
            from CREDITS
            order by ReleaseID, Job, CustomJob
        """)
        for release_id, rows in itertools.groupby(c, lambda row: row[1]):
            rows = list(rows)
            has_overall_authors = rows[0][4] == 0 and not rows[0][5]  # use credits with job = 0 as authors

            try:
                release = release_map[release_id]
            except KeyError:
                continue  # this release was skipped (probably because it was an unwanted prod type)

            # check whether this is an individual part / pack intro being aliased to the parent prod;
            # if it is, don't add its credits as an overall author
            is_alias = (release.janeway_id != release_id)

            author_name_ids = set()

            for credit_id, _, author_id, name_id, job, custom_job in rows:

                if name_id is None or name_id == 0:
                    # credited under primary name
                    try:
                        new_name_id = primary_name_id_map[author_id]
                    except KeyError:  # this author was skipped (probably because it was a BBS)
                        new_name_id = None
                else:
                    # credited under specific name
                    try:
                        new_name_id = name_id_map[name_id]
                    except KeyError:  # this name was skipped (probably because the author was a BBS)
                        new_name_id = None

                if new_name_id is None:
                    # can't add credits for this name
                    continue

                if ((not has_overall_authors) or (job == 0 and not custom_job)) and not is_alias:
                    # add this as an author
                    author_name_ids.add(new_name_id)

                if (job != 0 or custom_job):
                    # add as a credit
                    category, category_detail = JOBS[job]
                    if category_detail and custom_job:
                        description = "%s - %s" % (category_detail, custom_job)
                    else:
                        description = category_detail or custom_job or ''

                    Credit.objects.create(
                        janeway_id=credit_id, release=release, name_id=new_name_id,
                        category=category, description=description
                    )

            for name_id in author_name_ids:
                release.author_names.add(name_id)

        # Import soundtrack / graphic links
        print("Importing soundtrack links")
        c.execute("""
            select distinct FEATURES.ReleaseID, FEATURES.FeatureID
            from FEATURES
            INNER JOIN RELEASE_COMMONS on (FeatureID = RELEASE_COMMONS.ReleaseID and TagID = 799)
            where FeatureType = 0
        """)
        for release_id, feature_id in c:
            try:
                release = release_map[release_id]
            except KeyError:
                continue

            try:
                feature = release_map[feature_id]
            except KeyError:
                continue

            SoundtrackLink.objects.create(release=release, soundtrack=feature)
            # copy credits from soundtrack to the parent release
            for credit in Credit.objects.filter(release=feature):
                Credit.objects.create(
                    release=release, category='Music',
                    janeway_id=credit.janeway_id, name_id=credit.name_id, description=credit.description
                )

        print("Importing graphic credits")
        c.execute("""
            select distinct FEATURES.ReleaseID, FEATURES.FeatureID
            from FEATURES
            INNER JOIN RELEASE_COMMONS on (FeatureID = RELEASE_COMMONS.ReleaseID and TagID in (808, 813, 1630, 1632))
            where FeatureType = 0
        """)
        for release_id, feature_id in c:
            try:
                release = release_map[release_id]
            except KeyError:
                continue

            try:
                feature = release_map[feature_id]
            except KeyError:
                continue

            # copy credits from soundtrack to the parent release
            for credit in Credit.objects.filter(release=feature):
                Credit.objects.create(
                    release=release, category='Graphics',
                    janeway_id=credit.janeway_id, name_id=credit.name_id, description=credit.description
                )

        # Import download links
        print("Importing download links")
        c.execute("""
            select ID, ReleaseID, FileLink, FileType, Comment
            from FILES
            where FileType in (0,1,2,3,4)
            and FileLink <> ''
            and FileLink <> 'test'
        """)
        for janeway_id, release_id, link, file_type, comment in c:
            try:
                release = release_map[release_id]
            except KeyError:
                continue  # this release was skipped (probably because it was an unwanted prod type)

            url = expand(link, file_type)

            release.download_links.create(
                janeway_id=janeway_id, url=url, comment=(comment or '')
            )

        print("Removing music releases that only serve as soundtrack credits")
        Release.objects.filter(supertype='music', title__endswith='-unknown-', download_links__isnull=True).delete()
