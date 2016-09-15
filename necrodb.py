import config
import mysql.connector

class NecroDB():

    def _connect(self):
        self._db_conn = mysql.connector.connect(user=config.MYSQL_DB_USER, password=config.MYSQL_DB_PASSWD, host=config.MYSQL_DB_HOST, database=config.MYSQL_DB_NAME)

    def _close(self):
        self._db_conn.close()

    def set_prefs(self, params):
        self._connect()
        cursor = self._db_conn.cursor()
        cursor.execute("""INSERT INTO user_prefs (discord_id, hidespoilerchat, dailyalert, racealert) VALUES (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE discord_id=VALUES(discord_id), hidespoilerchat=VALUES(hidespoilerchat), dailyalert=VALUES(dailyalert), racealert=VALUES(racealert)""", params)
        self._db_conn.commit()
        self._close()

    def get_prefs(self, params):
        self._connect()
        cursor = self._db_conn.cursor()
        cursor.execute("""SELECT * FROM user_prefs WHERE discord_id=%s""", params)
        prefs = cursor.fetchall()
        self._close()
        return prefs

    def get_all_matching_prefs(self, type, params):
        if type == "hidespoilerchat":
            query = """SELECT discord_id FROM user_prefs WHERE hidespoilerchat=%s"""
        elif type == "dailyalert":
            query = """SELECT discord_id FROM user_prefs WHERE dailyalert=%s OR dailyalert=%s"""
        elif type == "racealert":
            query = """SELECT discord_id FROM user_prefs WHERE racealert=%s OR racealert=%s"""
        self._connect()
        cursor = self._db_conn.cursor()
        cursor.execute(query, params)
        prefs = cursor.fetchall()
        self._close()
        return prefs

    def record_race(self, race):
        self._connect()
        db_cur = self._db_conn.cursor(buffered=True)
        db_cur.execute("SELECT race_id FROM race_data ORDER BY race_id DESC LIMIT 1")
        new_raceid = 0
        for row in db_cur:
            new_raceid = row[0] + 1
            break

        race_params = (new_raceid,
                       race._start_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                       race.race_info.character,
                       race.race_info.descriptor,
                       race.race_info.flags,
                       race.race_info.seed,)
        db_cur.execute("INSERT INTO race_data (race_id, timestamp, character_name, descriptor, flags, seed) VALUES (%s,%s,%s,%s,%s,%s)", race_params)

        racer_list = []
        max_time = 0
        for r_id in race.racers:
            racer = race.racers[r_id]
            racer_list.append(racer)
            if racer.is_finished:
                max_time = max(racer.time, max_time)
        max_time += 1

        racer_list.sort(key=lambda r: r.time if r.is_finished else max_time)

        rank = 1
        for racer in racer_list:
            racer_params = (new_raceid, racer.id, racer.time, rank, racer.igt, racer.comment, racer.level)
            db_cur.execute("INSERT INTO racer_data (race_id, discord_id, time, rank, igt, comment, level) VALUES (%s,%s,%s,%s,%s,%s,%s)", racer_params)
            if racer.is_finished:
                rank += 1

            user_params = (racer.id, racer.name)
            db_cur.execute('INSERT INTO user_data (discord_id, name) VALUES (%s,%s) ON DUPLICATE KEY UPDATE discord_id=VALUES(discord_id), name=VALUES(name)', user_params)

        self._db_conn.commit()
        self._close()

    def register_all_users(self, members)
        self._connect()
        db_cur = self._db_conn.cursor(buffered=True)
        for member in members:
            params = (member.id, member.name,)
            db_cur.execute("INSERT IGNORE INTO user_data (discord_id, name) VALUES (%s,%s)", params)
        self._db_conn.commit()
        self._close()

    def register_user(self, member):
        self._connect()
        params = (member.id, member.name,)
        cursor = self._db_conn.cursor()
        cursor.execute("INSERT INTO user_data (discord_id, name) VALUES (%s,%s)", params)
        self.db_conn.commit()
        self._close()