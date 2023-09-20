import openpyxl  # conda install -c conda-forge openpyxl
from openpyxl.styles import PatternFill
import pandas as pd  # conda install -c conda-forge pandas
import datetime as dt


def convert_list(name, sheet, res_list):
    st = 0
    while len(res_list[st]) == 0:
        st += 1
    curr_date = res_list[st][0]['date']

    curr_flight = 0
    for i in range(st, len(res_list)):
        if len(res_list[i]) != 0:
            if curr_date != res_list[i][0]['date']:
                curr_date = res_list[i][0]['date']
                curr_flight = 0
            for j in range(len(res_list[i])):
                curr_flight += 1
                sheet.loc[sheet['date'] == curr_date, f"flight {curr_flight}"] = res_list[i][j]['time']

    sheet.dropna(axis=1, how='all', inplace=True)
    sheet.to_excel(name, index=False, engine='openpyxl')
    wb = openpyxl.load_workbook(name)
    ws = wb['Sheet1']
    alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K']

    letter = 0
    row = (sheet.index[sheet['date'] == curr_date][0]) + 2
    for i in range(len(res_list)):
        if len(res_list[i]) != 0:
            if curr_date != res_list[i][0]['date']:
                curr_date = res_list[i][0]['date']
                letter = 0
                row = (sheet.index[sheet['date'] == curr_date][0]) + 2

            for res_it in res_list[i]:
                letter += 1
                ws[str(alphabet[letter] + str(row))].fill = PatternFill(patternType='solid', fgColor=res_it['color'])

    wb.save(name)


def prepare_sheet(start, nums):
    res = pd.DataFrame(columns=['date', 'flight 1', 'flight 2', 'flight 3', 'flight 4', 'flight 5', 'flight 6',
                                'flight 7', 'flight 8', 'flight 9', 'flight 10', 'flight 11', 'flight 12'])
    res['date'] = [(start + dt.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(nums)]
    return res
