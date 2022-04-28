import re
import os
import sys
import fitz
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LTTextBoxHorizontal, LAParams
from pdfminer.pdfinterp import PDFTextExtractionNotAllowed


class PDF_Reader:

    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        py_path = sys.argv[0]
        py_dir = os.path.dirname(py_path)
        self.nations_path = os.path.join(py_dir, 'nations.txt')

    def PDF2Text(self, text_path=None):
        if text_path == None:
            text_path = self.pdf_path.replace('.pdf', '.txt')
        f = open(self.nations_path, "r")
        nations_list = f.read().splitlines()
        f.close()
        address_list = []
        email_list = []
        keywords = []
        references_list = []
        r = 0
        img_path = self.pdf_path.replace('.pdf', '.png')
        pdf = fitz.open(self.pdf_path)
        para_list = []
        for pg in range(0, pdf.pageCount):
            page = pdf[pg]
            trans = fitz.Matrix(5, 5).prerotate(0)
            pm = page.get_pixmap(matrix=trans, alpha=False)
            pm.save(img_path)
            para_list = ((pytesseract.image_to_string(
                Image.open(img_path))).split('\n\n'))
            for para_temp in para_list:
                para = para_temp
                for nation in nations_list:
                    para = ''.join([i for i in list(para) if i != '\n'])
                    if re.search('([^;]+,[\s]?'+nation+';)', para):
                        address_list.extend(
                            (re.findall('([^;]+,[\s]?'+nation+';)', para)).remove(';'))
                        break
                line_list = para.split('\n')
                for line in line_list:
                    for nation in nations_list:
                        if re.findall('(,[\s]?'+nation+'$)', line):
                            address_list.append(line)
                para = para_temp
                line_list = para.split('\n')
                for line in line_list:
                    for tuple in re.findall('([a-zA-Z-]+[\s]?(\.[a-zA-Z\s-]+?)*@([a-zA-Z\s-]+?\.)+[\s]?[a-zA-Z-]+)', line):
                        term = tuple[0]
                        email_list.append(term)
                para = para_temp
                if 'key' in para.lower() and 'words' in para.lower():
                    if len(para)-len('keywords') <= 5:
                        index = para_list.index(para)
                        keywords.append(
                            ''.join([i for i in list(para_list[index+1]) if i != '\n']))
                    else:
                        index = (para.lower()).find('key')
                        keywords.append(
                            ''.join([i for i in list(para[index:]) if i != '\n']))
                if 'index terms' in para.lower():
                    if len(para)-len('index terms') <= 5:
                        index = para_list.index(para)
                        keywords.append(
                            ''.join([i for i in list(para_list[index+1]) if i != '\n']))
                    else:
                        index = (para.lower()).find('index terms')
                        keywords.append(
                            ''.join([i for i in list(para[index:]) if i != '\n']))
                para = para_temp
                if r:
                    para = ''.join([i for i in list(para) if i != '\n'])
                    if len(para) >= 30:
                        references_list.append(para)
                elif 'references' == para.lower():
                    r = 1
                elif re.match('[\[][0-9]+[\]]', para):
                    r = 1
                    para = ''.join([i for i in list(para) if i != '\n'])
                    if len(para) >= 30:
                        references_list.append(para)
            os.remove(img_path)
        pdf.close()
        with open(text_path, "w") as f:
            f.write('Address: ' +
                    ','.join([i for i in address_list if i != '\n'])+'\n')
            f.write('Emails: ' +
                    ','.join([i for i in email_list if i != '\n'])+'\n')
            f.write('Keywords: ' +
                    ','.join([i for i in keywords if i != '\n'])+'\n')
            f.write('References: \n' +
                    '\n'.join([i for i in references_list if i != '\n'])+'\n')
        self.text = {'Address': address_list, 'Emails': email_list,
                     'Keywords': keywords, 'References': references_list}
        return True

    def PDF2Image(self, img_dir=None):
        self.image = []
        if img_dir == None:
            img_dir = self.pdf_path.replace('.pdf', '')
        if not os.path.exists(img_dir):
            os.makedirs(img_dir)
        fp = open(self.pdf_path, 'rb')
        parser = PDFParser(fp)
        doc = PDFDocument()
        parser.set_document(doc)
        doc.set_parser(parser)
        doc.initialize()
        if not doc.is_extractable:
            raise PDFTextExtractionNotAllowed
        else:
            rsrcmgr = PDFResourceManager()
            laparams = LAParams()
            device = PDFPageAggregator(rsrcmgr, laparams=laparams)
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            page_counts = 0
            for page in doc.get_pages():
                page_counts += 1
                interpreter.process_page(page)
                layout = device.get_result()
                pdf_size = layout.bbox
                layout_list = []
                for x in layout:
                    if(isinstance(x, LTTextBoxHorizontal)):
                        if (len("".join(filter(str.isalpha, x.get_text()))) >= 100 or re.match('[Ff][Ii][Gg]', x.get_text()) or re.match('[Tt][Aa][Bb][Ll][Ee]', x.get_text())) and 'Note' not in x.get_text() and 'NOTE' not in x.get_text():
                            layout_list.append(x)
                for x in layout_list:
                    if(isinstance(x, LTTextBoxHorizontal)):
                        try:
                            text = x.get_text()
                            text = ''.join(
                                [value for value in list(text) if value != '\n'])
                            for i in range(2):
                                img_regex = ['[Ff][Ii][Gg]',
                                             '[Tt][Aa][Bb][Ll][Ee]'][i]
                                img_type = ['Figure', 'Table'][i]
                                if re.match(img_regex, text):
                                    layout_index = layout_list.index(x)
                                    if layout_index >= 1 and layout_index <= len(layout_list)-2:
                                        last_object = layout_list[layout_index-1]
                                        next_object = layout_list[layout_index+1]
                                        if last_object.bbox[2] > next_object.bbox[3]:
                                            y0_pdf = next_object.bbox[3]
                                            y1_pdf = last_object.bbox[2]
                                        elif last_object.bbox[2] > x.bbox[3]:
                                            y0_pdf = 0
                                            y1_pdf = last_object.bbox[2]
                                        elif last_object.bbox[2] < x.bbox[3]:
                                            y0_pdf = next_object.bbox[3]
                                            y1_pdf = pdf_size[3]
                                    elif layout_index >= 1 and layout_index > len(layout_list)-2:
                                        last_object = layout_list[layout_index-1]
                                        y0_pdf = 0
                                        y1_pdf = last_object.bbox[2]
                                    elif layout_index < 1 and layout_index <= len(layout_list)-2:
                                        next_object = layout_list[layout_index+1]
                                        y0_pdf = next_object.bbox[3]
                                        y1_pdf = pdf_size[3]
                                    else:
                                        y0_pdf = 0
                                        y1_pdf = pdf_size[3]
                                    index = (
                                        re.match(img_regex+'[^0-9]*([0-9]+)', text)).group(1)
                                    img_name = img_type+'_'+index+'_Image'
                                    img_temp_name = img_type+'_'+index+'_Image_temp'
                                    text_name = img_type+'_'+index+'_Text'
                                    self.image.append(img_type+'_'+index)
                                    img_path = img_dir+'\\'+img_name+'.png'
                                    img_temp_path_1 = img_dir+'\\'+img_temp_name+'_1.png'
                                    img_temp_path_2 = img_dir+'\\'+img_temp_name+'_2.png'
                                    text_path = img_dir+'\\'+text_name+'.txt'
                                    images = convert_from_path(
                                        self.pdf_path, dpi=500, first_page=page_counts, last_page=page_counts)
                                    for image in images:
                                        image.save(img_temp_path_1, 'PNG')
                                    img = Image.open(img_temp_path_1)
                                    img_size = img.size
                                    x0_img = 0
                                    x1_img = img_size[0]
                                    y0_img = img_size[1]*(1-y1_pdf/pdf_size[3])
                                    y1_img = img_size[1]*(1-y0_pdf/pdf_size[3])
                                    cropped_img = img.crop(
                                        (x0_img, y0_img, x1_img, y1_img))
                                    if not os.path.exists(img_path):
                                        cropped_img.save(img_temp_path_2)
                                        f = open(text_path, 'a+',
                                                 encoding='utf-8')
                                        f.write(text)
                                        image = Image.open(img_temp_path_2)
                                        double = 0
                                        for x_temp in range(int(image.size[0]/3), int(2*image.size[0]/3)):
                                            divide_plane = 1
                                            for x_temp_line in range(int(x_temp), int(x_temp+0.016*image.size[0])):
                                                divide_line = 1
                                                for y_temp in range(int(image.size[1]/2), int(image.size[1])):
                                                    rgba = image.getpixel(
                                                        (x_temp_line, y_temp))
                                                    if rgba[0] != 255 or rgba[1] != 255 or rgba[2] != 255:
                                                        divide_line = 0
                                                        break
                                                if divide_line == 0:
                                                    divide_plane = 0
                                                    break
                                            if divide_plane == 1:
                                                double = 1
                                                x_crop = x_temp + \
                                                    0.008*image.size[0]
                                                break
                                        if double and x.bbox[0] < pdf_size[2]/3:
                                            cropped_image = image.crop(
                                                (0, 0, x_crop, image.size[1]))
                                            cropped_image.save(img_path)
                                        elif double and x.bbox[0] > pdf_size[2]/3:
                                            cropped_image = image.crop(
                                                (x_crop, 0, image.size[0], image.size[1]))
                                            cropped_image.save(img_path)
                                        else:
                                            image.save(img_path)
                                        os.remove(img_temp_path_2)
                                    os.remove(img_temp_path_1)
                        except:
                            continue


#if __name__ == '__main__':
pdf_path = "C:\\Users\\86191\\Downloads\\2111.06423.pdf"
pdf_reader = PDF_Reader(pdf_path)
if pdf_reader.PDF2Text():
    print(pdf_reader.text)
if pdf_reader.PDF2Image():
    print(pdf_reader.image)
