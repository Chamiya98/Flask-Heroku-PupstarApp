# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import mysql.connector

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="B@uR3123#",
    database="dog_care"
)

mycursor = mydb.cursor()

mycursor.execute("Select content from comments")

result = mycursor.fetchall()
badwordlist = []
# goodwords = []
for x in result:
    # print(x)
    # if search(x, "Best"):
    badwordlist.append(x)
    # print(x)
# else:
# goodwords.append(x)

# Press the green button in the gutter to run the script.
# if __name__ == '__main__':
#   print_hi('PyCharm')
print(badwordlist)
# print(goodwords)
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
