from tkinter import *
import random

def get_roll():
    min=1
    max=6

    die1 = random.randint(min,max)
    die2 = random.randint(min,max)

    if die1 == die2:
        print(die1,'+',die2,'=',die1+die2, '*** You rolled doubles ***')
    else:
        print(die1,'+',die2,'=',die1+die2)
    return die1,die2

def get_image(index):
    images = []
    images.append('die_01_42158_sm.gif')
    images.append('die_02_42159_sm.gif')
    images.append('die_03_42160_sm.gif')
    images.append('die_04_42161_sm.gif')
    images.append('die_05_42162_sm.gif')
    images.append('die_06_42164_sm.gif')
    return images[index-1]

counter = 0
def counter_label():
    global counter
    print('counter_label() counter =', counter)
    def count():
        global counter, imgLbl1, imgLbl2

        print('count() counter =', counter)

        print(counter)
        counter += 1
        if counter > 10:
           return

        die1, die2 = get_roll()

        imgfile1 = get_image(die1)
        imgLbl1.image = PhotoImage( file = imgfile1 )
        imgLbl1.configure( image = imgLbl1.image )

        imgfile2 = get_image(die2)
        imgLbl2.image = PhotoImage( file = imgfile2 )
        imgLbl2.configure( image = imgLbl2.image )

        imgLbl1.after(10, count)

    if counter >= 10:
        counter = 0
    count()

root = Tk()
root.title("Counting Seconds")

imgLbl1 = Label(root)
imgLbl1.pack(side =LEFT)
imgLbl2 = Label(root)
imgLbl2.pack(side =LEFT)

counter_label()

buttonr = Button(root, text='Roll', width=25, command=counter_label)
buttonr.pack()

buttonq = Button(root, text='Stop', width=25, command=root.destroy)
buttonq.pack()

root.mainloop()