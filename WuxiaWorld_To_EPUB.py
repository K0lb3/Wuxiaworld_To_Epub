from urllib.request import Request,urlopen  #page download
import json         #to extract some meta-data
import weasyprint   #html to pdf
import io           #weasyprint (bytes)->(io filestream) PyPDF2
import PyPDF2       #pdf editing and merging
import os

def requestPage(url):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    return urlopen(req).read()

def parsePage(html):
    #title=between(html,'<meta name="description" content="','">')
    chapter=between(html,'<div class="fr-view">','</div>')
    data={
        **json.loads(between(html,'<script type="application/ld+json">','</script>')),#author, date
        **json.loads(between(html,'<script>\n        var CHAPTER = ',';\n    </script>')),#title, prev/next chapter
        'chapter'   :   chapter[:chapter.rindex('</p>')]+'</p>',    #necessary to get rid of teasers and prev/next chapter links
    }
    return data

def FixData(data):
    #add/remove chapter title
    return data

def GeneratePDF(data):
    #set-up fine format
    #page/chapter, page/total pages
    #author, date

    #html to pdf (return as bytes)
    pdf = weasyprint.HTML(file_obj=data['chapter']).write_pdf()
    #bytes back to PyPDF2 pdf for editing
    pdf=PyPDF2.PdfFileReader(stream=io.BytesIO(pdf))
    #edit pdf

    return pdf

def between(text,begin,end):
    ret=text[text.index(begin)+len(begin):]
    return ret[:ret.index(end)]

def createPath(novel,chapter,path=''):
    invalidCharacter=['\\','/',':','?','"','<','>','|']   
    for c in invalidCharacter:
        novel=novel.replace(c,'')
        chapter=chapter.replace(c,'')
    
    path=os.path.join(path,novel)
    os.makedirs(path,exist_ok=True)
    return os.path.join(path,chapter)

#main procedure
if __name__ == '__main__':
    #input settings
    url=input('start chapter (url link):\t')
    mcount=int(input('chapters to load (0 for all):\t'))
    typ=input('HTML or PDF:\t').lower()

    if url[:26]!='https://www.wuxiaworld.com':
        input('Invalid url')
        exit()
    else:
        novel=between(url,'novel/','/').replace('-',' ').title()
    #download and convert chapters
    i=0
    mcount= mcount if mcount else 99999999  #ugly but it works just fine
    merger = PyPDF2.PdfFileMerger()
    while i<mcount and url: #loop through every chapter
        print(url[26:])
        #download page
        html = requestPage(url).decode('utf8')
        #extract relevant data
        try:
            data = parsePage(html)
        except ValueError:
            break   #some novels like CoS link to ``Hey there! You've caught up with the latest released chapter.``

        if typ=='pdf':
            #fix some stuff
            data=FixData(data)
            #generate pdf of the chapter and add it to the list
            merger.append(GeneratePDF(data))
        else:
            with open(createPath(novel,data['name'])+'.html','wb') as f:
                f.write(html.encode('utf8'))
        #prepare next round
        i+=1
        url = 'https://www.wuxiaworld.com%s'%data['nextChapter'] if data['nextChapter'] else False

    #merge pdfs and save result
    if typ=='pdf':
        merger.write("%s.pdf"%novel)