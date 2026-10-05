import sqlite3
import tkinter as tk
from tkinter import messagebox
from datetime import datetime


# ============================================================
# DATABASE
# ============================================================

conn = sqlite3.connect("atm_database.db")
cursor = conn.cursor()


# ============================================================
# USERS TABLE
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    account_number TEXT PRIMARY KEY,
    name TEXT,
    pin TEXT,
    balance REAL,
    locked INTEGER DEFAULT 0
)
""")

conn.commit()


# Old database compatibility
try:
    cursor.execute(
        "ALTER TABLE users ADD COLUMN locked INTEGER DEFAULT 0"
    )
    conn.commit()
except sqlite3.OperationalError:
    pass


# ============================================================
# TRANSACTIONS TABLE
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_number TEXT,
    transaction_type TEXT,
    amount REAL
)
""")

conn.commit()


# Add new columns if old database doesn't have them
try:
    cursor.execute(
        "ALTER TABLE transactions ADD COLUMN transaction_date TEXT"
    )
    conn.commit()
except sqlite3.OperationalError:
    pass


try:
    cursor.execute(
        "ALTER TABLE transactions ADD COLUMN balance_after REAL"
    )
    conn.commit()
except sqlite3.OperationalError:
    pass


# ============================================================
# ATM CASH TABLE
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS atm_cash (
    id INTEGER PRIMARY KEY,
    cash REAL
)
""")

conn.commit()


# ============================================================
# DEFAULT ACCOUNTS
# ============================================================

accounts = [
    ("10001", "Gunjan", "1234", 10000, 0),
    ("10002", "Rahul", "5678", 15000, 0),
    ("10003", "Priya", "2468", 20000, 0)
]


for account in accounts:

    cursor.execute(
        "SELECT account_number FROM users WHERE account_number = ?",
        (account[0],)
    )

    if cursor.fetchone() is None:

        cursor.execute("""
        INSERT INTO users
        (account_number, name, pin, balance, locked)
        VALUES (?, ?, ?, ?, ?)
        """, account)


conn.commit()


# ============================================================
# INITIAL ATM CASH
# ============================================================

cursor.execute(
    "SELECT cash FROM atm_cash WHERE id = 1"
)

if cursor.fetchone() is None:

    cursor.execute(
        "INSERT INTO atm_cash (id, cash) VALUES (1, 50000)"
    )

    conn.commit()


# ============================================================
# GLOBAL VARIABLES
# ============================================================

current_account = None

wrong_attempts = 0

MAX_ATTEMPTS = 3


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_user_name():

    cursor.execute(
        "SELECT name FROM users WHERE account_number = ?",
        (current_account,)
    )

    result = cursor.fetchone()

    if result:
        return result[0]

    return ""


def get_balance():

    cursor.execute(
        "SELECT balance FROM users WHERE account_number = ?",
        (current_account,)
    )

    result = cursor.fetchone()

    if result:
        return result[0]

    return 0


def get_atm_cash():

    cursor.execute(
        "SELECT cash FROM atm_cash WHERE id = 1"
    )

    result = cursor.fetchone()

    if result:
        return result[0]

    return 0


def get_current_datetime():

    return datetime.now().strftime(
        "%d-%m-%Y %H:%M:%S"
    )


# ============================================================
# RECEIPT
# ============================================================

def show_receipt(
        transaction_type,
        amount,
        balance,
        transaction_date):

    receipt_window = tk.Toplevel(root)

    receipt_window.title("ATM Receipt")

    receipt_window.geometry("430x500")

    receipt_window.resizable(False, False)


    tk.Label(
        receipt_window,
        text="🏧 ATM RECEIPT",
        font=("Arial", 20, "bold")
    ).pack(pady=20)


    tk.Label(
        receipt_window,
        text="----------------------------------------"
    ).pack()


    tk.Label(
        receipt_window,
        text=f"Account Number : {current_account}",
        font=("Arial", 12)
    ).pack(pady=8)


    tk.Label(
        receipt_window,
        text=f"Name : {get_user_name()}",
        font=("Arial", 12)
    ).pack(pady=8)


    tk.Label(
        receipt_window,
        text=f"Transaction : {transaction_type}",
        font=("Arial", 12)
    ).pack(pady=8)


    tk.Label(
        receipt_window,
        text=f"Amount : ₹{amount:.2f}",
        font=("Arial", 12)
    ).pack(pady=8)


    tk.Label(
        receipt_window,
        text=f"Balance : ₹{balance:.2f}",
        font=("Arial", 12, "bold")
    ).pack(pady=8)


    tk.Label(
        receipt_window,
        text=f"Date & Time : {transaction_date}",
        font=("Arial", 11)
    ).pack(pady=8)


    tk.Label(
        receipt_window,
        text="----------------------------------------"
    ).pack(pady=10)


    tk.Label(
        receipt_window,
        text="Thank You for using our ATM!",
        font=("Arial", 12, "bold")
    ).pack(pady=10)


    tk.Button(
        receipt_window,
        text="CLOSE",
        width=15,
        command=receipt_window.destroy
    ).pack(pady=15)


# ============================================================
# CHECK BALANCE
# ============================================================

def check_balance():

    balance = get_balance()

    messagebox.showinfo(
        "Account Balance",
        f"Account Number : {current_account}\n\n"
        f"Name : {get_user_name()}\n\n"
        f"Available Balance : ₹{balance:.2f}"
    )


# ============================================================
# WITHDRAW
# ============================================================

def withdraw_cash():

    amount_window = tk.Toplevel(root)

    amount_window.title("Withdraw Cash")

    amount_window.geometry("400x250")

    amount_window.resizable(False, False)


    tk.Label(
        amount_window,
        text="Enter Withdrawal Amount",
        font=("Arial", 14, "bold")
    ).pack(pady=20)


    amount_entry = tk.Entry(
        amount_window,
        font=("Arial", 14)
    )

    amount_entry.pack()


    def process_withdraw():

        amount_text = amount_entry.get().strip()


        if amount_text == "":

            messagebox.showerror(
                "Error",
                "Please enter an amount."
            )

            return


        try:

            amount = float(amount_text)

        except ValueError:

            messagebox.showerror(
                "Error",
                "Please enter a valid number."
            )

            return


        if amount <= 0:

            messagebox.showerror(
                "Error",
                "Amount must be greater than zero."
            )

            return


        if amount % 100 != 0:

            messagebox.showerror(
                "Error",
                "Withdrawal amount must be a multiple of ₹100."
            )

            return


        balance = get_balance()

        atm_cash = get_atm_cash()


        if amount > balance:

            messagebox.showerror(
                "Insufficient Balance",
                "You do not have enough balance."
            )

            return


        if amount > atm_cash:

            messagebox.showerror(
                "ATM Cash",
                "ATM does not have enough cash."
            )

            return


        new_balance = balance - amount

        new_atm_cash = atm_cash - amount

        transaction_date = get_current_datetime()


        cursor.execute("""
        UPDATE users
        SET balance = ?
        WHERE account_number = ?
        """, (new_balance, current_account))


        cursor.execute("""
        UPDATE atm_cash
        SET cash = ?
        WHERE id = 1
        """, (new_atm_cash,))


        cursor.execute("""
        INSERT INTO transactions
        (
            account_number,
            transaction_type,
            amount,
            transaction_date,
            balance_after
        )
        VALUES (?, ?, ?, ?, ?)
        """, (
            current_account,
            "WITHDRAW",
            amount,
            transaction_date,
            new_balance
        ))


        conn.commit()


        amount_window.destroy()


        messagebox.showinfo(
            "Success",
            f"₹{amount:.2f} withdrawn successfully!"
        )


        show_receipt(
            "WITHDRAW",
            amount,
            new_balance,
            transaction_date
        )


    tk.Button(
        amount_window,
        text="WITHDRAW",
        width=15,
        command=process_withdraw
    ).pack(pady=25)


# ============================================================
# DEPOSIT
# ============================================================

def deposit_cash():

    amount_window = tk.Toplevel(root)

    amount_window.title("Deposit Cash")

    amount_window.geometry("400x250")

    amount_window.resizable(False, False)


    tk.Label(
        amount_window,
        text="Enter Deposit Amount",
        font=("Arial", 14, "bold")
    ).pack(pady=20)


    amount_entry = tk.Entry(
        amount_window,
        font=("Arial", 14)
    )

    amount_entry.pack()


    def process_deposit():

        amount_text = amount_entry.get().strip()


        if amount_text == "":

            messagebox.showerror(
                "Error",
                "Please enter an amount."
            )

            return


        try:

            amount = float(amount_text)

        except ValueError:

            messagebox.showerror(
                "Error",
                "Please enter a valid number."
            )

            return


        if amount <= 0:

            messagebox.showerror(
                "Error",
                "Amount must be greater than zero."
            )

            return


        balance = get_balance()

        atm_cash = get_atm_cash()


        new_balance = balance + amount

        new_atm_cash = atm_cash + amount

        transaction_date = get_current_datetime()


        cursor.execute("""
        UPDATE users
        SET balance = ?
        WHERE account_number = ?
        """, (new_balance, current_account))


        cursor.execute("""
        UPDATE atm_cash
        SET cash = ?
        WHERE id = 1
        """, (new_atm_cash,))


        cursor.execute("""
        INSERT INTO transactions
        (
            account_number,
            transaction_type,
            amount,
            transaction_date,
            balance_after
        )
        VALUES (?, ?, ?, ?, ?)
        """, (
            current_account,
            "DEPOSIT",
            amount,
            transaction_date,
            new_balance
        ))


        conn.commit()


        amount_window.destroy()


        messagebox.showinfo(
            "Success",
            f"₹{amount:.2f} deposited successfully!"
        )


        show_receipt(
            "DEPOSIT",
            amount,
            new_balance,
            transaction_date
        )


    tk.Button(
        amount_window,
        text="DEPOSIT",
        width=15,
        command=process_deposit
    ).pack(pady=25)


# ============================================================
# MINI STATEMENT
# ============================================================

def mini_statement():

    statement_window = tk.Toplevel(root)

    statement_window.title("Mini Statement")

    statement_window.geometry("600x600")


    tk.Label(
        statement_window,
        text="🏧 ATM MINI STATEMENT",
        font=("Arial", 18, "bold")
    ).pack(pady=15)


    tk.Label(
        statement_window,
        text=f"Account: {current_account}    "
             f"Name: {get_user_name()}",
        font=("Arial", 11)
    ).pack(pady=5)


    text_box = tk.Text(
        statement_window,
        width=70,
        height=25,
        font=("Courier New", 10)
    )

    text_box.pack(
        padx=15,
        pady=15
    )


    scrollbar = tk.Scrollbar(
        statement_window,
        command=text_box.yview
    )

    scrollbar.pack(
        side=tk.RIGHT,
        fill=tk.Y
    )


    text_box.config(
        yscrollcommand=scrollbar.set
    )


    cursor.execute("""
    SELECT
        transaction_type,
        amount,
        transaction_date,
        balance_after
    FROM transactions
    WHERE account_number = ?
    ORDER BY id DESC
    LIMIT 10
    """, (current_account,))


    transactions = cursor.fetchall()


    if not transactions:

        text_box.insert(
            tk.END,
            "\nNo transactions found."
        )

    else:

        text_box.insert(
            tk.END,
            "==================================================\n"
        )

        text_box.insert(
            tk.END,
            "                 ATM STATEMENT\n"
        )

        text_box.insert(
            tk.END,
            "==================================================\n\n"
        )


        for transaction in transactions:

            transaction_type = transaction[0]

            amount = transaction[1]

            transaction_date = transaction[2]

            balance_after = transaction[3]


            if transaction_date is None:

                transaction_date = "Not Available"


            if balance_after is None:

                balance_text = "Not Available"

            else:

                balance_text = f"₹{balance_after:.2f}"


            text_box.insert(
                tk.END,
                f"Date    : {transaction_date}\n"
            )

            text_box.insert(
                tk.END,
                f"Type    : {transaction_type}\n"
            )

            text_box.insert(
                tk.END,
                f"Amount  : ₹{amount:.2f}\n"
            )

            text_box.insert(
                tk.END,
                f"Balance : {balance_text}\n"
            )

            text_box.insert(
                tk.END,
                "--------------------------------------------------\n"
            )


    text_box.config(
        state=tk.DISABLED
    )


# ============================================================
# CHANGE PIN
# ============================================================

def change_pin():

    pin_window = tk.Toplevel(root)

    pin_window.title("Change PIN")

    pin_window.geometry("400x400")

    pin_window.resizable(False, False)


    tk.Label(
        pin_window,
        text="Change ATM PIN",
        font=("Arial", 16, "bold")
    ).pack(pady=20)


    tk.Label(
        pin_window,
        text="Current PIN"
    ).pack()


    current_pin_entry = tk.Entry(
        pin_window,
        show="*"
    )

    current_pin_entry.pack(pady=5)


    tk.Label(
        pin_window,
        text="New PIN"
    ).pack()


    new_pin_entry = tk.Entry(
        pin_window,
        show="*"
    )

    new_pin_entry.pack(pady=5)


    tk.Label(
        pin_window,
        text="Confirm New PIN"
    ).pack()


    confirm_pin_entry = tk.Entry(
        pin_window,
        show="*"
    )

    confirm_pin_entry.pack(pady=5)


    def update_pin():

        current_pin = current_pin_entry.get()

        new_pin = new_pin_entry.get()

        confirm_pin = confirm_pin_entry.get()


        cursor.execute(
            "SELECT pin FROM users WHERE account_number = ?",
            (current_account,)
        )

        result = cursor.fetchone()


        if result is None:

            messagebox.showerror(
                "Error",
                "Account not found."
            )

            return


        if current_pin != result[0]:

            messagebox.showerror(
                "Error",
                "Current PIN is incorrect."
            )

            return


        if len(new_pin) != 4 or not new_pin.isdigit():

            messagebox.showerror(
                "Error",
                "New PIN must contain exactly 4 digits."
            )

            return


        if new_pin != confirm_pin:

            messagebox.showerror(
                "Error",
                "New PINs do not match."
            )

            return


        cursor.execute("""
        UPDATE users
        SET pin = ?
        WHERE account_number = ?
        """, (new_pin, current_account))


        conn.commit()


        messagebox.showinfo(
            "Success",
            "PIN changed successfully!"
        )


        pin_window.destroy()


    tk.Button(
        pin_window,
        text="CHANGE PIN",
        width=15,
        command=update_pin
    ).pack(pady=25)


# ============================================================
# ATM CASH STATUS
# ============================================================

def show_atm_cash():

    atm_cash = get_atm_cash()


    messagebox.showinfo(
        "ATM Cash Status",
        f"Current ATM Cash:\n\n₹{atm_cash:.2f}"
    )


# ============================================================
# LOGOUT
# ============================================================

def logout():

    global current_account
    global wrong_attempts


    current_account = None

    wrong_attempts = 0

    login_screen()


# ============================================================
# USER ATM MENU
# ============================================================

def atm_menu():

    for widget in root.winfo_children():

        widget.destroy()


    tk.Label(
        root,
        text="🏧 ATM MACHINE",
        font=("Arial", 22, "bold")
    ).pack(pady=20)


    tk.Label(
        root,
        text=f"Welcome, {get_user_name()}",
        font=("Arial", 14)
    ).pack(pady=5)


    tk.Label(
        root,
        text=f"Account: {current_account}",
        font=("Arial", 11)
    ).pack(pady=5)


    tk.Button(
        root,
        text="CHECK BALANCE",
        width=25,
        command=check_balance
    ).pack(pady=7)


    tk.Button(
        root,
        text="WITHDRAW CASH",
        width=25,
        command=withdraw_cash
    ).pack(pady=7)


    tk.Button(
        root,
        text="DEPOSIT CASH",
        width=25,
        command=deposit_cash
    ).pack(pady=7)


    tk.Button(
        root,
        text="MINI STATEMENT",
        width=25,
        command=mini_statement
    ).pack(pady=7)


    tk.Button(
        root,
        text="CHANGE PIN",
        width=25,
        command=change_pin
    ).pack(pady=7)


    tk.Button(
        root,
        text="ATM CASH STATUS",
        width=25,
        command=show_atm_cash
    ).pack(pady=7)


    tk.Button(
        root,
        text="LOGOUT",
        width=25,
        command=logout
    ).pack(pady=7)


    tk.Button(
        root,
        text="EXIT",
        width=25,
        command=root.destroy
    ).pack(pady=7)


# ============================================================
# ADMIN LOGIN
# ============================================================

def admin_login_screen():

    admin_window = tk.Toplevel(root)

    admin_window.title("Admin Login")

    admin_window.geometry("400x350")

    admin_window.resizable(False, False)


    tk.Label(
        admin_window,
        text="🔐 ADMIN LOGIN",
        font=("Arial", 20, "bold")
    ).pack(pady=30)


    tk.Label(
        admin_window,
        text="Username",
        font=("Arial", 12)
    ).pack(pady=5)


    username_entry = tk.Entry(
        admin_window,
        font=("Arial", 13)
    )

    username_entry.pack()


    tk.Label(
        admin_window,
        text="Password",
        font=("Arial", 12)
    ).pack(pady=10)


    password_entry = tk.Entry(
        admin_window,
        font=("Arial", 13),
        show="*"
    )

    password_entry.pack()


    def verify_admin():

        username = username_entry.get().strip()

        password = password_entry.get().strip()


        if username == "admin" and password == "1234":

            admin_window.destroy()

            admin_panel()

        else:

            messagebox.showerror(
                "Login Failed",
                "Invalid Admin Username or Password."
            )


    tk.Button(
        admin_window,
        text="LOGIN",
        width=18,
        command=verify_admin
    ).pack(pady=25)


# ============================================================
# ADMIN - ATM CASH STATUS
# ============================================================

def admin_cash_status():

    cash = get_atm_cash()


    messagebox.showinfo(
        "ATM Cash",
        f"Current ATM Cash:\n\n₹{cash:.2f}"
    )


# ============================================================
# ADMIN - REFILL ATM CASH
# ============================================================

def refill_atm_cash():

    refill_window = tk.Toplevel(root)

    refill_window.title("ATM Cash Refill")

    refill_window.geometry("400x300")

    refill_window.resizable(False, False)


    tk.Label(
        refill_window,
        text="💰 ATM CASH REFILL",
        font=("Arial", 18, "bold")
    ).pack(pady=25)


    tk.Label(
        refill_window,
        text=f"Current ATM Cash: ₹{get_atm_cash():.2f}",
        font=("Arial", 12)
    ).pack(pady=10)


    tk.Label(
        refill_window,
        text="Enter Refill Amount"
    ).pack(pady=5)


    amount_entry = tk.Entry(
        refill_window,
        font=("Arial", 13)
    )

    amount_entry.pack()


    def process_refill():

        amount_text = amount_entry.get().strip()


        if amount_text == "":

            messagebox.showerror(
                "Error",
                "Please enter amount."
            )

            return


        try:

            amount = float(amount_text)

        except ValueError:

            messagebox.showerror(
                "Error",
                "Enter a valid amount."
            )

            return


        if amount <= 0:

            messagebox.showerror(
                "Error",
                "Amount must be greater than zero."
            )

            return


        new_cash = get_atm_cash() + amount


        cursor.execute("""
        UPDATE atm_cash
        SET cash = ?
        WHERE id = 1
        """, (new_cash,))


        conn.commit()


        messagebox.showinfo(
            "Success",
            f"₹{amount:.2f} added to ATM.\n\n"
            f"New ATM Cash: ₹{new_cash:.2f}"
        )


        refill_window.destroy()


    tk.Button(
        refill_window,
        text="REFILL ATM",
        width=18,
        command=process_refill
    ).pack(pady=25)


# ============================================================
# ADMIN - VIEW ALL ACCOUNTS
# ============================================================

def view_all_accounts():

    account_window = tk.Toplevel(root)

    account_window.title("All Accounts")

    account_window.geometry("700x500")


    tk.Label(
        account_window,
        text="👥 ALL ATM ACCOUNTS",
        font=("Arial", 18, "bold")
    ).pack(pady=15)


    text_box = tk.Text(
        account_window,
        width=85,
        height=23,
        font=("Courier New", 10)
    )

    text_box.pack(
        padx=10,
        pady=10
    )


    cursor.execute("""
    SELECT
        account_number,
        name,
        balance,
        locked
    FROM users
    ORDER BY account_number
    """)


    users = cursor.fetchall()


    text_box.insert(
        tk.END,
        "===========================================================\n"
    )

    text_box.insert(
        tk.END,
        " Account       Name          Balance          Status\n"
    )

    text_box.insert(
        tk.END,
        "===========================================================\n"
    )


    for user in users:

        account_number = user[0]

        name = user[1]

        balance = user[2]

        locked = user[3]


        if locked == 1:

            status = "LOCKED"

        else:

            status = "ACTIVE"


        line = (
            f" {account_number:<13}"
            f"{name:<14}"
            f"₹{balance:<15.2f}"
            f"{status}\n"
        )


        text_box.insert(
            tk.END,
            line
        )


    text_box.config(
        state=tk.DISABLED
    )


# ============================================================
# ADMIN - UNLOCK ACCOUNT
# ============================================================

def unlock_account():

    unlock_window = tk.Toplevel(root)

    unlock_window.title("Unlock Account")

    unlock_window.geometry("400x300")

    unlock_window.resizable(False, False)


    tk.Label(
        unlock_window,
        text="🔓 UNLOCK ACCOUNT",
        font=("Arial", 18, "bold")
    ).pack(pady=30)


    tk.Label(
        unlock_window,
        text="Enter Account Number"
    ).pack(pady=5)


    account_entry_admin = tk.Entry(
        unlock_window,
        font=("Arial", 13)
    )

    account_entry_admin.pack()


    def process_unlock():

        account_number = account_entry_admin.get().strip()


        if account_number == "":

            messagebox.showerror(
                "Error",
                "Please enter account number."
            )

            return


        cursor.execute("""
        SELECT name, locked
        FROM users
        WHERE account_number = ?
        """, (account_number,))


        result = cursor.fetchone()


        if result is None:

            messagebox.showerror(
                "Error",
                "Account does not exist."
            )

            return


        name = result[0]

        locked = result[1]


        if locked == 0:

            messagebox.showinfo(
                "Account Status",
                f"{name}'s account is already active."
            )

            return


        cursor.execute("""
        UPDATE users
        SET locked = 0
        WHERE account_number = ?
        """, (account_number,))


        conn.commit()


        messagebox.showinfo(
            "Success",
            f"Account {account_number} has been unlocked."
        )


        unlock_window.destroy()


    tk.Button(
        unlock_window,
        text="UNLOCK ACCOUNT",
        width=20,
        command=process_unlock
    ).pack(pady=25)


# ============================================================
# ADMIN PANEL
# ============================================================

def admin_panel():

    admin_window = tk.Toplevel(root)

    admin_window.title("ATM Admin Panel")

    admin_window.geometry("500x600")

    admin_window.resizable(False, False)


    tk.Label(
        admin_window,
        text="🔐 ATM ADMIN PANEL",
        font=("Arial", 22, "bold")
    ).pack(pady=30)


    tk.Label(
        admin_window,
        text="Administrator Controls",
        font=("Arial", 12)
    ).pack(pady=5)


    tk.Button(
        admin_window,
        text="ATM CASH STATUS",
        width=28,
        command=admin_cash_status
    ).pack(pady=12)


    tk.Button(
        admin_window,
        text="REFILL ATM CASH",
        width=28,
        command=refill_atm_cash
    ).pack(pady=12)


    tk.Button(
        admin_window,
        text="VIEW ALL ACCOUNTS",
        width=28,
        command=view_all_accounts
    ).pack(pady=12)


    tk.Button(
        admin_window,
        text="UNLOCK ACCOUNT",
        width=28,
        command=unlock_account
    ).pack(pady=12)


    tk.Button(
        admin_window,
        text="CLOSE ADMIN PANEL",
        width=28,
        command=admin_window.destroy
    ).pack(pady=30)


# ============================================================
# USER LOGIN
# ============================================================

def login():

    global current_account
    global wrong_attempts


    account_number = account_entry.get().strip()

    pin = pin_entry.get().strip()


    if account_number == "" or pin == "":

        messagebox.showerror(
            "Error",
            "Please enter Account Number and PIN."
        )

        return


    cursor.execute("""
    SELECT name, pin, locked
    FROM users
    WHERE account_number = ?
    """, (account_number,))


    result = cursor.fetchone()


    if result is None:

        messagebox.showerror(
            "Login Failed",
            "Account does not exist."
        )

        return


    name = result[0]

    correct_pin = result[1]

    locked = result[2]


    if locked == 1:

        messagebox.showerror(
            "Account Locked",
            "This account is locked.\n\n"
            "Please contact the administrator."
        )

        return


    if pin == correct_pin:

        current_account = account_number

        wrong_attempts = 0


        messagebox.showinfo(
            "Login Successful",
            f"Welcome {name}!"
        )


        atm_menu()

        return


    wrong_attempts += 1


    remaining_attempts = MAX_ATTEMPTS - wrong_attempts


    if wrong_attempts >= MAX_ATTEMPTS:

        cursor.execute("""
        UPDATE users
        SET locked = 1
        WHERE account_number = ?
        """, (account_number,))


        conn.commit()


        messagebox.showerror(
            "Account Locked",
            "3 wrong PIN attempts.\n\n"
            "Your account has been locked."
        )


        return


    messagebox.showerror(
        "Wrong PIN",
        f"Incorrect PIN.\n\n"
        f"Remaining attempts: {remaining_attempts}"
    )


# ============================================================
# LOGIN SCREEN
# ============================================================

def login_screen():

    global account_entry
    global pin_entry


    for widget in root.winfo_children():

        widget.destroy()


    tk.Label(
        root,
        text="🏧 ATM LOGIN",
        font=("Arial", 24, "bold")
    ).pack(pady=35)


    tk.Label(
        root,
        text="Account Number",
        font=("Arial", 12)
    ).pack(pady=5)


    account_entry = tk.Entry(
        root,
        width=25,
        font=("Arial", 14)
    )

    account_entry.pack(pady=5)


    tk.Label(
        root,
        text="PIN",
        font=("Arial", 12)
    ).pack(pady=5)


    pin_entry = tk.Entry(
        root,
        width=25,
        font=("Arial", 14),
        show="*"
    )

    pin_entry.pack(pady=5)


    tk.Button(
        root,
        text="LOGIN",
        width=20,
        command=login
    ).pack(pady=20)


    # ADMIN BUTTON

    tk.Button(
        root,
        text="ADMIN LOGIN",
        width=20,
        command=admin_login_screen
    ).pack(pady=5)


    tk.Label(
        root,
        text="Demo Accounts",
        font=("Arial", 12, "bold")
    ).pack(pady=15)


    tk.Label(
        root,
        text="10001 / 1234\n"
             "10002 / 5678\n"
             "10003 / 2468",
        font=("Arial", 10)
    ).pack()


# ============================================================
# MAIN WINDOW
# ============================================================

root = tk.Tk()

root.title("ATM Simulation")

root.geometry("450x700")

root.resizable(False, False)


login_screen()


# ============================================================
# RUN
# ============================================================

root.mainloop()


# ============================================================
# CLOSE DATABASE
# ============================================================

conn.close()