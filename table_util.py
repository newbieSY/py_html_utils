#--*--encoding:utf-8--*--
'''
主要提供编辑table的功能，包括：删除行、删除列、增加行、增加列
1、删除行：主要指删除一个tr,主要就是修改跟改行相关的rowspan
2、删除列：主要指删除一个td,主要涉及到相关的colspan

'''
from bs4 import BeautifulSoup

def delete_row_col(trs,param):
    '''
    删除指定的行或列
    填充表格，将colspan和rowspan省略掉的td补充出来,然后删掉该行，修改其上rowspan 等行的值
    定义：如果删除的行带rowspan值,则只需要删除独自内容部分，共享部分（rowspan部分保留即放入下一行）
    :param trs: 表格的所有trs
    :param param: {"tr":2,"td":2}
    :return:
    '''
    INSERT_TD_TEXT="TT"
    # 先根据rowspan和colspan补充出为二维数组,每个元素放（td,rowspan_td）
    tds_arr = supply_table(trs, INSERT_TD_TEXT)
    if "tr" in param:
        delete_tr = param["tr"]
        delete_row(tds_arr,delete_tr,INSERT_TD_TEXT)
    elif "td" in param:
        delete_td = param["td"]
        delete_col(trs,tds_arr,delete_td,INSERT_TD_TEXT)
        #删完列需要检测一下，是否有行下已经没有td了，则样的行直接删除
        detect_delete_nulltr(trs,tds_arr)
def detect_delete_nulltr(trs,tds_arr):
    '''
    检测是否存在只有tr标记的空行，将其删除
    :param trs:
    :return:
    '''
    for i,each_tr in enumerate(trs):
        tds= each_tr.find_all("td")
        update_td=[]
        if tds is None or len(tds)==0:
            #需要修改该行扩展出来source td,修改rospan
            for each_td_inarr in tds_arr[i]:
                if "rowspan" in each_td_inarr[1].attrs and each_td_inarr[1] not in update_td:
                    each_td_inarr[1]["rowspan"]=int(each_td_inarr[1]["rowspan"])-1
                    update_td.append(each_td_inarr[1])
            each_tr.extract()
def delete_col(trs,tds_arr,delete_td,INSERT_TD_TEXT):
    '''
    删除指定列
    :param tds_arr:
    :param delete_tr:
    :param INSERT_TD_TEXT:
    :return:
    '''
    update_td = []
    fellow_next_td_tds = []  #   需要保留信息的td [(td,row)]
    for row in range(len(tds_arr)):
        if delete_td<len(tds_arr[row]):
            #如果为extend_td删除，然后source_td的colspan-1
            if tds_arr[row][delete_td][0].text==INSERT_TD_TEXT and \
                tds_arr[row][delete_td][1] not in update_td and \
                    tds_arr[row][delete_td][1] not in [temp[0] for temp in fellow_next_td_tds]:
                if "colspan" in tds_arr[row][delete_td][1].attrs:
                    tds_arr[row][delete_td][1]["colspan"]=int(tds_arr[row][delete_td][1]["colspan"])-1
                    update_td.append(tds_arr[row][delete_td][1])
            #如果为source_td且带colspan,则将colspan-1和text传到下一列
            if tds_arr[row][delete_td][0].text!=INSERT_TD_TEXT:
                if "colspan" in  tds_arr[row][delete_td][0].attrs and int(tds_arr[row][delete_td][0]["colspan"])>1:
                    fellow_next_td_tds.append((tds_arr[row][delete_td][0],row))
                tds_arr[row][delete_td][0].extract()
    # 在该行找到一个不是extend_td, 先从后面找找到在其后插入一个td,否则再从前面找找到在其前面插入td
    for each_fellow_next_td_tds in fellow_next_td_tds:
        row=each_fellow_next_td_tds[1]
        text = tds_arr[row][delete_td][0].text
        rowspan = int(tds_arr[row][delete_td][0]["rowspan"]) if "rowspan" in tds_arr[row][delete_td][0].attrs else 1
        colspan = int(tds_arr[row][delete_td][0]["colspan"]) - 1
        bs = BeautifulSoup("<td rowspan=\"%d\" colspan=\"%d\">%s</td>" % (
            rowspan, colspan, text),
                           "html.parser")
        post_find=False
        for i in range(delete_td+1,len(tds_arr[each_fellow_next_td_tds[1]]),1):
            if tds_arr[row][i][0].text!=INSERT_TD_TEXT:
                tds_arr[row][i][0].insert_before(bs)
                tds_arr[row][delete_td]=(tds_arr[row][i][0].previous_sibling,tds_arr[row][delete_td][1])
                post_find=True
                break
        if post_find==False:
            for i in range(delete_td-1,-1,-1):
                if tds_arr[row][i][0].text!=INSERT_TD_TEXT:
                    tds_arr[row][i][0].insert_after(bs)
                    tds_arr[row][delete_td]=(tds_arr[row][i][0].next_sibling,tds_arr[row][delete_td][1])
                    post_find=True
                    break
        #如果都没有找到，说明删除该td后没有节点了，在tr中插入td只是将colspan-1
        if post_find==False:
            trs[row].insert(0,bs)

def delete_row(tds_arr,delete_tr,INSERT_TD_TEXT):
    '''
    删除指定行
    :param tds_arr:
    :param delete_tr:
    :param INSERT_TD_TEXT:
    :return:
    '''
    # 以便在删除时能更好的找到需要修改的rowspan、然后删除行，删除行与colspan无关
    update_td = []  # 从同一个td扩展出来的只需要修改一次rowspan即可
    fellow_next_tr_tds = []  #   需要保留信息的td [(td,index)]
    for i, each_tds_tuple in enumerate(tds_arr):
        if i == delete_tr:
            for j, each_td_tuple in enumerate(each_tds_tuple):
                if "rowspan" in each_td_tuple[0].attrs and int(each_td_tuple[0]["rowspan"])>1:  # (source_td,source_td)
                    fellow_next_tr_tds.append((each_td_tuple[0], j))
                elif "rowspan" in each_td_tuple[1].attrs and \
                        each_td_tuple[1] not in [temp[0] for temp in fellow_next_tr_tds] and \
                        each_td_tuple[
                            1] not in update_td:  # (extend_td,source_td)同一行有多个extent_td,或者有一个source_td,另外有该td的extent_td的处理一次
                    each_td_tuple[1]["rowspan"] = int(each_td_tuple[1]["rowspan"]) - 1
                    update_td.append(each_td_tuple[1])
            # 在其下一行找到一个不是extend_td, 先从前面找找到在其后插入一个td,再从后面找找到在其前面插入td
            if i + 1 < len(tds_arr):
                find_source_td = None
                for m, each_fellow_next_tr_tds in enumerate(fellow_next_tr_tds):
                    rowspan = int(each_fellow_next_tr_tds[0]["rowspan"]) - 1
                    colspan = int(each_fellow_next_tr_tds[0][
                                      "colspan"]) if "colspan" in each_fellow_next_tr_tds[0].attrs else 1
                    bs = BeautifulSoup("<td rowspan=\"%d\" colspan=\"%d\">%s</td>" % (
                        rowspan, colspan, each_fellow_next_tr_tds[0].text),
                                       "html.parser")
                    pre_find=False
                    for k in range(each_fellow_next_tr_tds[1]-1, -1, -1):  # 向前找
                        if tds_arr[i + 1][k][0].text != INSERT_TD_TEXT:
                            tds_arr[i + 1][k][0].insert_after(bs)
                            # tds_arr[i+1][each_fellow_next_tr_tds[1]][0]=tds_arr[i+1][k][0].next_sibling
                            tds_arr[i + 1][each_fellow_next_tr_tds[1]] = (
                            tds_arr[i + 1][k][0].next_sibling, tds_arr[i + 1][each_fellow_next_tr_tds[1]][1])
                            pre_find=True
                            break
                    if  pre_find==False:
                        for k in range(each_fellow_next_tr_tds[1]+1, len(tds_arr[i + 1]), 1):  # 向后找
                            if tds_arr[i + 1][k][0].text != INSERT_TD_TEXT:
                                tds_arr[i + 1][k][0].insert_before(bs)
                                # tds_arr[i+1][each_fellow_next_tr_tds[1]][0]=tds_arr[i+1][k][0].next_sibling
                                tds_arr[i + 1][each_fellow_next_tr_tds[1]] = (
                                    tds_arr[i + 1][k][0].previous_sibling, tds_arr[i + 1][each_fellow_next_tr_tds[1]][1])
                                break
            trs[i].extract()
            break
def get_index(tds,td_object):
    # 确定在trs中的位置
    index=-1
    for l in range(len(tds)):
        if tds[l] is td_object:
            index=l
            break
    return index
def supply_table(trs,insert_td_text):
    '''
    填充表格，将colspan和rowspan省略掉的td补充出来
    :param trs:
    :param insert_td_text:填充的td的文本
    :return[[(insert_td,source_td),()],[]]
    '''
    # 获取header的td最大数
    max_td_num = 0
    for each_td in trs[0].find_all("td"):
        if "colspan" in each_td.attrs:
            max_td_num += int(each_td["colspan"]) - 1
        max_td_num += 1
    tds_arr = [[None] * max_td_num for i in range(len(trs))]

    bs = BeautifulSoup("<td>%s</td>" % (insert_td_text), "html.parser")
    for i, each_tr in enumerate(trs):
        offset=0
        for j, each_td in enumerate(each_tr.find_all("td")):
            rowspan = 1
            if "rowspan" in each_td.attrs:
                rowspan = int(each_td["rowspan"])
            colspan = 1
            if "colspan" in each_td.attrs:
                colspan = int(each_td["colspan"])
            #从当前行找到第一个为None的，下标即是offset
            for k,each_td_temp in enumerate(tds_arr[i]):
                if each_td_temp is None:
                    offset=k
                    break
            for row in range(0, rowspan, 1):
                for col in range(0, colspan, 1):
                    if row == 0 and col == 0:
                        tds_arr[i][offset] = (each_td, each_td)
                    else:
                        tds_arr[i + row][offset + col] = (bs.td, each_td)
    return tds_arr
def get_headerstr_index(trs,header_str):
    '''
    根据所给的表头关键字，查询列索引,默认第一行为表头
    :param trs:
    :param header_str:
    :return:
    '''
    index=-1
    INSERT_TD_TEXT='insert_into_temp_td_str'
    if trs is not None and len(trs)>0:
        # 先根据rowspan和colspan补充出为二维数组,每个元素放（td,rowspan_td）
        tds_arr = supply_table(trs, INSERT_TD_TEXT)
        for i,each_td in enumerate(tds_arr[0]):
            if header_str in each_td[0].text:
                index=i
                break
    return index
if __name__=="__main__":
        # while True:
        bs = BeautifulSoup(open("./table.html"), "html.parser")
        table = bs.find("table")
        trs = table.find_all("tr")
        index=get_headerstr_index(trs, "22")
        # if index==-1:
        #     break
        if index>=0:
            delete_row_col(trs,{"td":index})
        with open("./table.html","w",encoding="utf-8") as fopen:
            fopen.write(str(bs))
    # bs = BeautifulSoup("<tr><td>3</td><td>2</td></tr>", "html.parser")
    # bs1 = BeautifulSoup("<td>4</td>", "html.parser")
    # bs2 = BeautifulSoup("<td>5</td>", "html.parser")
    # td=bs.find("td")
    # print(td)
    # td.insert_after(bs1)
    # print(td.next_sibling)
