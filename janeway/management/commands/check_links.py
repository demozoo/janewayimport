from django.core.management.base import BaseCommand
import MySQLdb

from janeway.links import expand


class Command(BaseCommand):
    def handle(self, **options):
        mysql = MySQLdb.connect(user='janeway', db='janeway', passwd='janeway')

        c = mysql.cursor()

        c.execute("""
            select ID, ReleaseID, FileLink, FileType
            from FILES
            where FileType in (0,1,2,3,4)
            and FileLink <> ''
            and FileLink <> 'test'
        """)
        for janeway_id, release_id, link, filetype in c:
            try:
                expand(link, filetype)
            except ValueError:
                raise Exception("unrecognised link for ID %d: %s (type %d)" % (release_id, link, filetype))
