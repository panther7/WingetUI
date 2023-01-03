from PySide6.QtCore import *
import subprocess, time, os, sys
from tools import *
from tools import _


common_params = ["--source", "winget", "--accept-source-agreements"]

#winget = "powershell -ExecutionPolicy ByPass -Command [Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
winget = "chcp 65001 && mode con: cols=500 && "
if getSettings("UseSystemWinget"):
    winget = winget + " winget.exe"
else:
    winget = winget + " winget-cli/winget.exe"
    # winget = f"{winget} {0}".format(os.path.abspath(f"{realpath}/winget-cli/winget.exe"));


def searchForPackage(signal: Signal, finishSignal: Signal, noretry: bool = False) -> None:
    print(f"🟢 Starting winget search...")
    #p = subprocess.Popen(["mode", "400,30&", "winget.exe", "search", ""] + common_params ,stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ.copy(), shell=True)
    p = subprocess.Popen(f"{winget} search \"\" {' '.join(common_params)}", stderr=subprocess.STDOUT, env=os.environ.copy(), shell=True, encoding="utf-8")
    output = []
    counter = 0
    idSeparator = 0
    for line in p.stdout.readlines():
        if(counter > 0):
            output.append(line)
        else:
            l = line.replace("\x08-\x08\\\x08|\x08 \r","")
            l = l.split("\r")[-1]
            if("Id" in l):
                idSeparator = len(l.split("Id")[0])
                verSeparator = idSeparator+2
                i=0
                while l.split("Id")[1].split(" ")[i] == "":
                    verSeparator += 1
                    i += 1
                counter += 1
    print(p.stdout)
    print(p.stderr)
    if p.returncode != 0 and not noretry:
        time.sleep(1)
        print(p.returncode)
        searchForPackage(signal, finishSignal, noretry=True)
    else:
        counter = 0
        for element in output:
            try:
                verElement = element[idSeparator:]
                verElement.replace("\t", " ")
                while "  " in verElement:
                    verElement = verElement.replace("  ", " ")
                iOffset = 0
                id = verElement.split(" ")[iOffset+0]
                try:
                    ver = verElement.split(" ")[iOffset+1]
                except IndexError:
                    ver = _("Unknown")
                if len(id)==1:
                    iOffset + 1
                    id = verElement.split(" ")[iOffset+0]
                    try:
                        ver = verElement.split(" ")[iOffset+1]
                    except IndexError:
                        ver = "Unknown"
                if ver in ("<", "-", ""):
                    iOffset += 1
                    ver = verElement.split(" ")[iOffset+1]
                if not "  " in element[0:idSeparator]:
                    signal.emit(element[0:idSeparator], id, ver, "Winget")
                else:
                    print(f"🟡 package {element[0:idSeparator]} failed parsing, going for method 2...")
                    print(element, verSeparator)
                    export = (element[0:idSeparator], element[idSeparator:].split(" ")[0], list(filter(None, element[idSeparator:].split(" ")))[1])
                    signal.emit(export[0], export[1], export[2], "Winget")
            except Exception as e:
                try:
                    report(e)
                    signal.emit(element[0:idSeparator], element[idSeparator:verSeparator], element[verSeparator:].split(" ")[0], "Winget")
                except Exception as e:
                    report(e)
        print("🟢 Winget search finished")
        finishSignal.emit("winget")  # type: ignore

def searchForOnlyOnePackage(id: str) -> tuple[str, str]:
    print(f"🟢 Starting winget search id {id}...")
    p = subprocess.Popen(f"{winget} search --id {id.replace('…', '')} {' '.join(common_params)}", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, env=os.environ.copy(), shell=True, encoding="utf-8")
    counter = 0
    idSeparator = 0
    while p.poll() is None:
        line = p.stdout.readline()
        line = line.strip()
        if line:
            if(counter > 0):
                if not "---" in line:
                    return str(line[:idSeparator], errors="ignore").strip(), str(line[idSeparator:], errors="ignore").split(" ")[0].strip()
            else:
                l = str(line, errors="ignore").replace("\x08-\x08\\\x08|\x08 \r","")
                l = l.split("\r")[-1]
                if("Id" in l):
                    idSeparator = len(l.split("Id")[0])
                    verSeparator = idSeparator+2
                    i=0
                    while l.split("Id")[1].split(" ")[i] == "":
                        verSeparator += 1
                        i += 1
                    counter += 1
    return (id, id)

def searchForUpdates(signal: Signal, finishSignal: Signal, noretry: bool = False) -> None:
    print(f"🟢 Starting winget upgrade...")
    p = subprocess.Popen(f"{winget} upgrade --include-unknown {' '.join(common_params[0:2])}", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ.copy(), shell=True, encoding="utf-8")
    output: list[str] = []
    counter = 0
    idSeparator = 0
    print("AAA")
    # print(f"upgrade {p.stdout.readlines()}")
    while p.poll() is None:
        line = p.stdout.readline().strip()
        print(line)
        if line:
            if(counter > 0):
                if not "upgrades available" in line:
                    output.append(line)
            else:
                l = line.replace("\x08-\x08\\\x08|\x08 \r","")
                for char in ("\r", "/", "|", "\\", "-"):
                    l = l.split(char)[-1]
                print(l)
                if("Id" in l):
                    idSeparator = len(l.split("Id")[0])
                    verSeparator = len(l.split("Version")[0])
                    newVerSeparator = len(l.split("Available")[0])
                    counter += 1
    print("BBB")

    if p.returncode != 0 and not noretry:
        time.sleep(1)
        print(p.returncode)
        searchForUpdates(signal, finishSignal, noretry=True)
    else:
        counter = 0
        for element in output:
            try:
                verElement = element[idSeparator:]
                verElement.replace("\t", " ")
                while "  " in verElement:
                    verElement = verElement.replace("  ", " ")
                iOffset = 0
                id = verElement.split(" ")[iOffset+0]
                ver = verElement.split(" ")[iOffset+1]
                newver = verElement.split(" ")[iOffset+2]
                if len(id)==1:
                    iOffset + 1
                    id = verElement.split(" ")[iOffset+0]
                    newver = verElement.split(" ")[iOffset+2]
                    ver = verElement.split(" ")[iOffset+1]
                if ver in ("<", ">", "-"):
                    iOffset += 1
                    ver = verElement.split(" ")[iOffset+1]
                    newver = verElement.split(" ")[iOffset+2]
                if not "  " in element[0:idSeparator]:
                    signal.emit(element[0:idSeparator], id, ver, newver, "Winget")
                else:
                    print(f"🟡 package {element[0:idSeparator]} failed parsing, going for method 2...")
                    print(element, verSeparator)
                    name = element[0:idSeparator].replace("  ", "#").replace("# ", "#").replace(" #", "#")
                    while "##" in name:
                        name = name.replace("##", "#")
                    signal.emit(name.split("#")[0], name.split("#")[-1]+id, ver, newver, "Winget")
            except Exception as e:
                try:
                    signal.emit(element[0:idSeparator], element[idSeparator:verSeparator], element[verSeparator:newVerSeparator].split(" ")[0], element[newVerSeparator:].split(" ")[0], "Winget")
                except Exception as e:
                    report(e)
        print("🟢 Winget search finished")
        finishSignal.emit("winget")

def searchForInstalledPackage(signal: Signal, finishSignal: Signal) -> None:
    print(f"🟢 Starting winget list...")
    p = subprocess.Popen(f"{winget} list {' '.join(common_params)}", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ.copy(), shell=True, encoding="utf-8")
    output = []
    counter = 0
    idSeparator = 0
    while p.poll() is None:
        line = p.stdout.readline()
        line = line.strip()
        if line:
            if(counter > 0 and not "---" in line):
                output.append(line)
            else:
                l = str(line, errors="ignore").replace("\x08-\x08\\\x08|\x08 \r","")
                for char in ("\r", "/", "|", "\\", "-"):
                    l = l.split(char)[-1].strip()
                if("Id" in l):
                    idSeparator = len(l.split("Id")[0])
                    verSeparator = len(l.split("Version")[0])
                    counter += 1
    counter = 0
    emptyStr = ""
    wingetName = "Winget"
    for element in output:
        try:
            element = str(element, errors="ignore")
            element = element.replace("2010  x", "2010 x").replace("Microsoft.VCRedist.2010", " Microsoft.VCRedist.2010") # Fix an issue with MSVC++ 2010, where it shows with a double space (see https://github.com/marticliment/WingetUI#450)
            verElement = element[idSeparator:].strip()
            verElement.replace("\t", " ")
            while "  " in verElement:
                verElement = verElement.replace("  ", " ")
            iOffset = 0
            id = verElement.split(" ")[iOffset+0]
            ver = verElement.split(" ")[iOffset+1]
            if len(id)==1:
                iOffset + 1
                id = verElement.split(" ")[iOffset+0]
                ver = verElement.split(" ")[iOffset+1]
            if ver.strip() in ("<", "-"):
                iOffset += 1
                ver = verElement.split(" ")[iOffset+1]
            if not "  " in element[0:idSeparator].strip():
                signal.emit(element[0:idSeparator].strip(), id, ver, wingetName)
            else:
                print(f"🟡 package {element[0:idSeparator].strip()} failed parsing, going for method 2...")
                print(element, verSeparator)
                name = element[0:idSeparator].strip().replace("  ", "#").replace("# ", "#").replace(" #", "#")
                while "##" in name:
                    name = name.replace("##", "#")
                signal.emit(name.split("#")[0], name.split("#")[-1]+id, ver, wingetName)
        except Exception as e:
            try:
                report(e)
                element = str(element)
                signal.emit(element[0:idSeparator].strip(), element[idSeparator:].strip(), emptyStr, wingetName)
            except Exception as e:
                report(e)
    print("🟢 Winget uninstallable packages search finished")
    finishSignal.emit("winget")

def getInfo(signal: Signal, title: str, id: str, useId: bool) -> None:
    try:
        oldid = id
        id = id.replace("…", "")
        oldtitle = title
        title = title.replace("…", "")
        if "…" in oldid:
            title, id = searchForOnlyOnePackage(oldid)
            oldid = id
            oldtitle = title
            useId = True
        elif "…" in oldtitle:
            title = searchForOnlyOnePackage(oldid)[0]
            oldtitle = title
        validCount = 0
        iterations = 0
        while validCount < 2 and iterations < 50:
            iterations += 1
            if useId:
                p = subprocess.Popen([winget, "show", "--id", f"{id}", "--exact"]+common_params, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ.copy(), shell=True)
                print(f"🟢 Starting get info for id {id}")
            else:
                p = subprocess.Popen([winget, "show", "--name", f"{title}", "--exact"]+common_params, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ.copy(), shell=True)
                print(f"🟢 Starting get info for title {title}")
            output = []
            unknownStr = _("Unknown")
            appInfo = {
                "title": oldtitle,
                "id": oldid,
                "publisher": unknownStr,
                "author": unknownStr,
                "description": unknownStr,
                "homepage": unknownStr,
                "license": unknownStr,
                "license-url": unknownStr,
                "installer-sha256": unknownStr,
                "installer-url": unknownStr,
                "installer-type": unknownStr,
                "updatedate": unknownStr,
                "releasenotes": unknownStr,
                "manifest": f"https://github.com/microsoft/winget-pkgs/tree/master/manifests/{id[0].lower()}/{'/'.join(id.split('.'))}",
                "versions": []
            }
            while p.poll() is None:
                line = p.stdout.readline()
                line = line.strip()
                cprint(line)
                if line:
                    output.append(str(line, errors="ignore"))
            print(p.stdout)
            for line in output:
                cprint(line)
                if("Publisher:" in line):
                    appInfo["publisher"] = line.replace("Publisher:", "").strip()
                    validCount += 1
                elif("Description:" in line):
                    appInfo["description"] = line.replace("Description:", "").strip()
                    validCount += 1
                elif("Author:" in line):
                    appInfo["author"] = line.replace("Author:", "").strip()
                    validCount += 1
                elif("Publisher:" in line):
                    appInfo["publisher"] = line.replace("Publisher:", "").strip()
                    validCount += 1
                elif("Homepage:" in line):
                    appInfo["homepage"] = line.replace("Homepage:", "").strip()
                    validCount += 1
                elif("License:" in line):
                    appInfo["license"] = line.replace("License:", "").strip()
                    validCount += 1
                elif("License Url:" in line):
                    appInfo["license-url"] = line.replace("License Url:", "").strip()
                    validCount += 1
                elif("SHA256:" in line):
                    appInfo["installer-sha256"] = line.replace("SHA256:", "").strip()
                    validCount += 1
                elif("Download Url:" in line):
                    appInfo["installer-url"] = line.replace("Download Url:", "").strip()
                    validCount += 1
                elif("Release Date:" in line):
                    appInfo["updatedate"] = line.replace("Release Date:", "").strip()
                    validCount += 1
                elif("Release Notes Url:" in line):
                    url = line.replace("Release Notes Url:", "").strip()
                    appInfo["releasenotes"] = f"<a href={url} style='color:%bluecolor%'>{url}</a>"
                    validCount += 1
                elif("Type:" in line):
                    appInfo["installer-type"] = line.replace("Type:", "").strip()
        print(f"🟢 Loading versions for {title}")
        retryCount = 0
        output = []
        while output == [] and retryCount < 50:
            retryCount += 1
            if useId:
                p = subprocess.Popen([winget, "show", "--id", f"{id}", "-e", "--versions"]+common_params, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ.copy(), shell=True)
            else:
                p = subprocess.Popen([winget, "show", "--name",  f"{title}", "-e", "--versions"]+common_params, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ.copy(), shell=True)
            counter = 0
            print(p.args)
            while p.poll() is None:
                line = p.stdout.readline()
                line = line.strip()
                if line:
                    if(counter > 2):
                        output.append(str(line, errors="ignore"))
                    else:
                        counter += 1
            cprint("Output: ")
            cprint(output)
        appInfo["versions"] = output
        signal.emit(appInfo)
    except Exception as e:
        report(e)
    
def installAssistant(p: subprocess.Popen, closeAndInform: Signal, infoSignal: Signal, counterSignal: Signal) -> None:
    print(f"🟢 winget installer assistant thread started for process {p}")
    outputCode = 0
    counter = 0
    output = ""
    while p.poll() is None:
        line = p.stdout.readline()
        line = line.strip()
        line = str(line, errors="ignore").strip()
        if line:
            infoSignal.emit(line)
            counter += 1
            counterSignal.emit(counter)
            output += line+"\n"
    p.wait()
    outputCode = p.returncode
    if outputCode == 0x8A150011:
        outputCode = 2
    closeAndInform.emit(outputCode, output)
 
def uninstallAssistant(p: subprocess.Popen, closeAndInform: Signal, infoSignal: Signal, counterSignal: Signal) -> None:
    print(f"🟢 winget installer assistant thread started for process {p}")
    outputCode = 0
    counter = 0
    output = ""
    while p.poll() is None:
        line = p.stdout.readline()
        line = line.strip()
        line = str(line, errors="ignore").strip()
        if line:
            infoSignal.emit(line)
            counter += 1
            counterSignal.emit(counter)
            output += line+"\n"
    p.wait()
    outputCode = p.returncode
    if "1603" in output:
        outputCode = 1603
    closeAndInform.emit(outputCode, output)



if(__name__=="__main__"):
    import __init__