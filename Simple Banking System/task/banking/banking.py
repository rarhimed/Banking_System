import random
import sqlite3


class Bank:

    menu = {
        0: "\n1. Create an account\n2. Log into account\n0. Exit",
        1: "\n1. Balance\n2. Add income\n3. Do transfer\n4. Close account\n5. Log out\n0. Exit"
    }

    def __init__(self):
        self.accounts = {}
        self.state = 0  # 0 - Main menu; 1 - Account menu
        self.current_user = None
        self.current_balance = None
        self.conn = Bank.connect_db()
        self.cur = self.conn.cursor()

    def create_account(self):
        # 1. Generate id
        last_id = self.sql_last_id()
        user_id = last_id + 1 if last_id is not None else 1
        # 2. Generate card number
        user_card = self.sql_generate_card(last_id)
        # 3. Generatr pin
        user_pin = str(random.randrange(1000, 9999))
        # 4. Save new account data
        self.sql_save_account(user_id, user_card, user_pin)
        print('Your card has been created')
        print('Your card number:', user_card, sep='\n')
        print('Your card PIN:', user_pin, sep='\n')

    def log_in(self):
        card = input('Enter your card number:\n')
        pin = input('Enter your PIN:\n')
        # 1. Check account credentials
        account_cmd = """SELECT * FROM card
        WHERE number = {}
        AND pin = {};""".format(card, pin)
        credentials = self.cur.execute(account_cmd).fetchone()
        if credentials is None:
            print('\nWrong card number or PIN!')
        else:
            print('\nYou have successfully logged in!')
            self.current_user = credentials[1]
            self.current_balance = credentials[3]
            self.change_state()

    def log_out(self):
        self.current_user = None
        self.current_balance = None
        print('You have successfully logged out!')
        self.change_state()

    def get_balance(self):
        print('Balance:', self.current_balance)

    def change_state(self):
        self.state = 0 if self.state == 1 else 1

    def add_income(self):
        money = int(input('Enter income:\n'))
        if money > 0:
            self.current_balance += money
            self.sql_update_balance(self.current_user, self.current_balance)
        print('Income was added!')

    def do_transfer(self):
        recipient = input('Transfer\nEnter card number:\n')
        recipient_data_cmd = """SELECT *
        FROM card
        WHERE number = {};""".format(recipient)
        recipient_data = self.cur.execute(recipient_data_cmd).fetchone()
        recipient_exists = True if recipient_data is not None else False
        # 1. Check card by Luhn
        if recipient[-1] != self.luhn_number(recipient[:-1]):
            print('Probably you made a mistake in the card number. Please try again!')
        # 2. Check card in DB
        elif not recipient_exists:
            print('Such a card does not exist.')
        # 3. Check card on owner - is it current user?
        elif self.current_user == recipient:
            print("You can't transfer money to the same account!")
        else:
            money = int(input('Enter how much money you want to transfer:\n'))
            # 4. Check balance
            if self.current_balance < money:
                print('Not enough money!')
            else:
                # 4.1. Update sender balance
                self.current_balance -= money
                self.sql_update_balance(self.current_user, self.current_balance)
                # 4.2. Update recipient balance
                recipient_balance = recipient_data[3] + money
                self.sql_update_balance(recipient, recipient_balance)
                print('Success!')

    def close_account(self):
        delete_cmd = """DELETE FROM card
        WHERE number = {};""".format(self.current_user)
        self.cur.execute(delete_cmd)
        self.conn.commit()
        print('The account has been closed!')
        self.change_state()

    def run(self):
        commands = {
            0: {1: self.create_account,
                2: self.log_in},
            1: {1: self.get_balance,
                2: self.add_income,
                3: self.do_transfer,
                4: self.close_account,
                5: self.log_out}
        }
        print(Bank.menu[self.state])
        while True:
            command = int(input())
            print()
            if command == 0:
                print('Bye!')
                break
            else:
                commands[self.state][command]()
                print(Bank.menu[self.state])

    def sql_update_balance(self, card, money):
        income_cmd = """UPDATE card
                    SET balance = {}
                    WHERE number = {};""".format(money, card)
        self.cur.execute(income_cmd)
        self.conn.commit()

    def sql_last_id(self):
        max_id_cmd = """SELECT max(id) FROM card;"""
        max_id = self.cur.execute(max_id_cmd).fetchone()[0]
        return max_id

    def sql_generate_card(self, last_id):
        if last_id is not None:
            number_cmd = """SELECT number FROM card
            WHERE id = {};""".format(last_id)
            last_number = self.cur.execute(number_cmd).fetchone()[0]
        else:
            last_number = '4000001111111111'
        card_number = str(int(last_number[:-1]) + 1)
        card_number += Bank.luhn_number(card_number)
        return card_number

    def sql_save_account(self, id, number, pin):
        insert_cmd = """INSERT INTO card (id, number, pin, balance)
        VALUES ({0}, {1}, {2}, 0);""".format(id, number, pin)
        self.cur.execute(insert_cmd)
        self.conn.commit()

    @staticmethod
    def luhn_number(nums):
        temp_nums = [int(num) for num in nums]
        # Multiply odd digits by 2
        for i in range(0, len(temp_nums), 2):
            temp_nums[i] *= 2
        # Substrate 9 from numbers over 9
        for i in range(0, len(temp_nums), 2):
            if temp_nums[i] > 9:
                temp_nums[i] -= 9
        # Sum all numbers
        total_sum = sum(temp_nums)
        mod = total_sum % 10
        if mod != 0:
            luhn_num = 10 - mod
        else:
            luhn_num = 0

        return str(luhn_num)

    @staticmethod
    def connect_db(db_name='card'):
        conn = sqlite3.connect(f'{db_name}.s3db')
        cur = conn.cursor()
        try:
            cur.execute('SELECT * FROM card LIMIT 1')
        except:
            cur.execute('CREATE TABLE card(id INTEGER, number TEXT, pin TEXT, balance INTEGER DEFAULT 0);')
            conn.commit()
        finally:
            return conn


my_bank = Bank()
my_bank.run()
