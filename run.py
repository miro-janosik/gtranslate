import os
#from googletrans import Translator
from google.cloud import translate
import html

project_id = "my-translate-50019"
assert project_id
parent = f"projects/{project_id}"
client = translate.TranslationServiceClient()

languages = { 
	"arabic" : "ar", 
	"czech" : "cs", 
	"croatian" : "hr", 
	"english" : "en", 
	"german" : "de", 
	"greek" : "el", 
	"farsi" : "fa", 
	"french" : "fr", 
	"polish" : "pl", 
	"romanian" : "ro", 
	"russian" : "ru", 
	"slovak" : "sk", 
	"spanish" : "es",
	"swedish" : "sv", 
	"vietnamese" : "vi"
	}

def walkFolder(folder : str):
	# for root, dirs, files in os.walk(folder):
	files = os.listdir(folder)
	foundFiles = []
	
	# get the .lab files from the local folder
	for name in files:
		if name.endswith((".lab")): # , ".txt"
			foundFiles.append( name )
	
	return foundFiles

def remoteTranslation( lang : str, textToTranslate : list ) -> str :
	if lang == "en":
		return textToTranslate
	
	response = client.translate_text(
		contents=textToTranslate,
		source_language_code=lang,
		target_language_code="en",
		parent=parent
	)
	
	r = []
	for translation in response.translations:
		# to avoid html encoding
		r.append(html.unescape(translation.translated_text))
	return r

errors = []

# file consists of lines like:
# 23.842099	28.625000	B:pl01M:english:* hello. sorry i don't speak German.
def translateFile( inFileName : str, outFileName : str ):
	
	# split the lines by the language
	# grouping together lines in the same language can lower the amount of requests
	# these will be stored in [langs]
	langs = {}
	
	# all the original lines will be stored in lines; after translation they will be updated and written to output
	lines = []
	
	with open(inFileName, 'r', newline='') as lab:

		lineNumber = -1
		for lineText in lab:
			lineNumber += 1
			
			l = lineText.strip()
			items = l.split('\t')
			
			# line contains: start time, end time, side and speaker, language, orig text, translated text
			line = []

			if len(items) != 3:
				errors.append(f"line {lineNumber} does not have 3 items")
				lines.append(line)
				continue
			
			i = items[2].split(':')
			if len(i) != 4:
				errors.append(f"line {lineNumber} does not have 3 items")
				lines.append(line)
				continue
			
			line.append( items[0] )
			line.append( items[1] )
			line.append( f"{i[0]}:{i[1]}" )
			line.append( i[2] )
			line.append( i[3] )
			lines.append(line)
			
			lang = i[2]
			if lang in languages:
				lang = languages[lang]
			else:
				errors.append(f"line {lineNumber} incorrect language {lang}")
				continue
			
			text = i[3]
			textTest = text.strip().strip('*').strip('-').strip()
			if not textTest:
				# empty string
				continue
			
			# update the language request with new request text line
			l = []
			if lang in langs:
				l = langs.get( lang )
			
			l.append( ( lineNumber, text ) )

			langs[ lang ] = l
	
	numLangs = len(langs)
	print(f"Going to translate {numLangs} languages.")
	
	langKeys = langs.keys()
	for lang in langKeys:
		texts = langs[ lang ]
		textToTranslate = []
		for textItems in texts:
			textToTranslate.append(textItems[1])
		
		# call the translator
		translatedLines = remoteTranslation(lang, textToTranslate)
		
		if len(translatedLines) != len(texts):
			errors.append( f"Translated output has {len(translatedLines)} instead of {len(texts)} for lang {lang}")
			continue
		
		for i in range(len(texts)):
			lineIndex = texts[i][0]
			translatedText = translatedLines[i]
			lines[ lineIndex ].append( translatedText )
	
	# Now take the lines and put them out
	
	with open(outFileName, 'wt') as lab:
		
		lineIndex = -1
		for l in lines:
			lineIndex += 1
			# line contains: start time, end time, side:speaker, language, orig text, translated text
			if len(l) < 5:
				errors.append(f"line {lineIndex} is read properly")
				continue
			
			# it was not translated, for some reason, then keep original
			lang = l[3]
			text = l[4]
			if len(l) == 6:
				lang = "english"
				text = l[5]
			
			lab.write(f"{l[0]}\t{l[1]}\t{l[2]}:{lang}:{text}\n")
	

def translateFolder( inFolder : str, outFolder : str, fileNames : list ):
	
	for fileName in fileNames:
		
		fullInName = os.path.join(inFolder, fileName)
		fullOutName = os.path.join(outFolder, fileName)
		
		#print(f"Checking {fileName}")
		translateFile( fullInName, fullOutName )
		
		if errors:
			print(f"File {fileName} errors:")
			for error in errors:
				print(error)
				
			errors.clear()
		


fileNames = walkFolder("./in")
translateFolder("./in", "./out", fileNames)

#t = remoteTranslation("de", ["Hallo, wo bist du?", "Ich warte hier", "Kurtze zeit"])
#print (t)
