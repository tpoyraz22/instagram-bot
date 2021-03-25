from selenium import webdriver
from time import sleep
from datetime import datetime
from selenium.webdriver.chrome.options import Options
import sqlite3


class Database:

    def __init__(self):
        conn = None
        self.first_time = True
        try:
            conn = sqlite3.connect("instabot.db")
        finally:
            self.conn = conn
        self.cur = self.conn.cursor()
        self.cur.execute("CREATE TABLE IF NOT EXISTS unfollowers (name VARCHAR(30), date VARCHAR(30));")
        self.cur.execute("CREATE TABLE IF NOT EXISTS new_followers (name VARCHAR(30), date VARCHAR(30));")
        try:
            self.cur.execute("CREATE TABLE refreshed_followers (name VARCHAR(30), UNIQUE(name));")
        except:
            self.first_time = False
            self.cur.execute("DROP TABLE IF EXISTS pre_refresh_followers")
            self.cur.execute("ALTER TABLE refreshed_followers RENAME TO pre_refresh_followers")
            self.cur.execute("CREATE TABLE refreshed_followers(name VARCHAR(30), UNIQUE(name))")
        self.refreshed_followers = []

    def insert_follower(self, follower):
        try:
            sql = "INSERT INTO refreshed_followers(name) VALUES (?);"
            self.cur.execute(sql, (follower,))
            self.conn.commit()
            self.refreshed_followers.append(follower)
        except:
            pass

    def compare(self):
        if not self.first_time:
            sql = "SELECT DISTINCT name FROM pre_refresh_followers WHERE name NOT IN (SELECT DISTINCT name FROM refreshed_followers)"
            unfollowers = self.cur.execute(sql).fetchall()
            for i in range(len(unfollowers)):
                sql = "INSERT INTO unfollowers(name, date) VALUES (?,?) "
                now = datetime.now()
                dt_string = now.strftime("%d/%m/%Y %H:%M")
                self.cur.execute(sql, (unfollowers[i][0], dt_string))
                self.conn.commit()

            sql = "SELECT DISTINCT name FROM refreshed_followers WHERE name NOT IN (SELECT DISTINCT name FROM pre_refresh_followers)"
            new_followers = self.cur.execute(sql).fetchall()
            for i in range(len(new_followers)):
                sql = "INSERT INTO new_followers(name, date) VALUES (?,?)"
                now = datetime.now()
                dt_string = now.strftime("%d/%m/%Y %H:%M")
                self.cur.execute(sql, (new_followers[i][0], dt_string))
                self.conn.commit()

class InstaBot:
    def __init__(self, username, password, headless=False):
        self.driver = webdriver.Chrome()
        if headless:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
        self.driver.get("http://www.instagram.com")
        sleep(2)
        self.driver.find_element_by_xpath("/html/body/div[1]/section/main/article/div[2]/div[1]/div/form/div/div[1]/div/label/input").send_keys(username)
        self.driver.find_element_by_xpath("/html/body/div[1]/section/main/article/div[2]/div[1]/div/form/div/div[2]/div/label/input").send_keys(password)
        self.driver.find_element_by_xpath("/html/body/div[1]/section/main/article/div[2]/div[1]/div/form/div/div[3]/button").click()
        sleep(4)
        self.driver.find_element_by_xpath("/html/body/div[1]/section/main/div/div/div/div/button").click()
        self.driver.find_element_by_xpath("/html/body/div[4]/div/div/div/div[3]/button[2]").click()

        self.username = username

    def get_unfollowers(self):
        self.driver.get(f"https://www.instagram.com/{self.username}")
        self.driver.find_element_by_xpath("//a[contains(@href, '/followers')]").click()
        sleep(1)
        scroll_box = self.driver.find_element_by_xpath("/html/body/div[5]/div/div/div[2]")
        last_ht, ht = 0, 1
        while last_ht != ht:
            last_ht = ht
            sleep(1)
            ht = self.driver.execute_script("""
                arguments[0].scrollTo(0, arguments[0].scrollHeight);
                return arguments[0].scrollHeight;
                """, scroll_box)

        links = scroll_box.find_elements_by_tag_name('a')
        self.followers = [link.text for link in links if link != '']

if __name__ == "__main__":
    username, password, headless = input("Enter username: "), input("Enter password: "), input(
        "Run in the background? Y or N: ").lower()
    while True:
        if headless == "y":
            my_bot = InstaBot(username, password, True)
        elif headless == "n":
            my_bot = InstaBot(username, password)
        else:
            print("Invalid input. Terminating.")
            break
        my_bot.get_unfollowers()
        my_bot.driver.close()
        my_db = Database()
        for follower in my_bot.followers:
            my_db.insert_follower(follower)
        my_db.compare()
        sleep(3600)