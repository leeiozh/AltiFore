import openpyxl
from openpyxl.styles import PatternFill
import pandas as pd
import datetime as dt


def convert_list(name_sheet, sheet, list):
    st = 0
    while len(list[st]) == 0:
        st += 1
    curr_date = list[st][0]['date']

    k = 0
    for i in range(st, len(list)):
        if len(list[i]) != 0:
            if curr_date != list[i][0]['date']:
                curr_date = list[i][0]['date']
                k = 0
            for j in range(len(list[i])):
                k += 1
                sheet.loc[sheet['date'] == curr_date, ("flight" + str(k))] = str(list[i][j]['time'])

    sheet.to_excel(name_sheet, index=False, engine='openpyxl')
    wb = openpyxl.load_workbook(name_sheet)
    ws = wb['Sheet1']
    alhpabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K']
    d = (sheet.index[sheet['date'] == curr_date][0]) + 2

    for i in range(len(list)):
        if len(list[i]) != 0:

            if curr_date != list[i][0]['date']:
                curr_date = list[i][0]['date']
                k = 0
                d = (sheet.index[sheet['date'] == curr_date][0]) + 2

            for j in range(len(list[i])):
                k += 1
                ws[str(alhpabet[k] + str(d))].fill = PatternFill(patternType='solid', fgColor=list[i][j]['color'])

    wb.save(name_sheet)


def prepare_sheet(start, nums):
    res = pd.DataFrame(columns=['date'])
    res['date'] = [(start + dt.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(nums)]
    return res
