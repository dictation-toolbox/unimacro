#probably not used anymore (Quintijn)
import os.path

def convertTo83Path(fullPath,removeSpacesOnly=0):
    """tries to convert (valid) long path names to Dos83 pathnames

    """
    if fullPath.find('-') >= 0:
        print('found "-", dos83 ignore: %s'% fullPath)
        return fullPath
    # only possible if fullPath exists.
    # no garantee that the converted path refers to the same location
    # I have not found standard functions for this conversion,
    # nor do I know how to compare equivalence: os.path.samefile is not available in Win
    # Are there any winApi calls?
    if not os.path.exists(fullPath):
        print('Path conversion failed. This is not a valid path:')
        print(fullPath)
        return ''
    # go try convert
    (name,ext)=os.path.splitext (fullPath)
    splitPath=name.split('\\')
    splitPath83=splitPath[:]
    for subPath in splitPath:
        concatPath=''.join(subPath.split())
        if (concatPath!=subPath) or ((not removeSpacesOnly) and (len(subPath)>8)):
            # convert subpath to Dos 8.3 convention
            concatPath=concatPath[0:min(6,len(concatPath))]
            i=splitPath.index(subPath)
            altConcatPath=[]
            for n in range(1,10): # try simple rule and find those that exist
                splitPath83[i]=concatPath+'~'+str(n)
                Path83=' '.join(splitPath83,'\\')+ext
                if os.path.exists(Path83):
                    if os.stat(Path83)==os.stat(fullPath):
                        altConcatPath.append(concatPath+'~'+str(n))
            # how many existing with matching stats did we find?        
            if len(altConcatPath)==1:
                splitPath83[i]=altConcatPath[0]
            elif len(altConcatPath)>1:
                splitPath83[i]=altConcatPath[0]
                print('Warning. Non unique Path conversion.')
            else:
                splitPath83[i]=concatPath+'??'
                print('Warning. Insufficient rule for conversion.')
    Path83=' '.join(splitPath83,'\\')+ext
    if not os.path.exists(Path83):
        print('Path conversion failed. This is not a valid Dos 8.3 path:')
        print(Path83)
        return ''
    else:    
        return Path83

def convertSpacedSubPaths(fullPath):
    return convertTo83Path(fullPath,removeSpacesOnly=1)

print(convertTo83Path('C:\Program Files'))#print convertTo83Path('C:\Program Files\Common Files\Microsoft Shared\MSCREATE.DIR')#print convertTo83Path('C:\Program Files\ArrayVisualizer\SAMPLES\SAMPLES.HTM')#print convertSpacedSubPaths('C:\Program Files\ArrayVisualizer\SAMPLES\SAMPLES.HTM')