#!/usr/bin/python

import sys
from typing import NamedTuple
import optparse

example = """
<File>
<Include name="string"/>
<Namespace name="a.b.c">
    <Record name="BaseRecord">
        <Field name="field1" type="int"/>
        <Field name="field2" type="std::string"/>
    </Record>
    <Record name="DerivedRecord" extends="BaseRecord">
        <Field name="field3" type="int"/>
        <Field name="field4" type="const char*"/>
        <Field name="field5" type=""/>
    </Record>

</Namespace>
</File>

"""

alternateSyntax = """
#include <string>
namespace a.b.c {
    struct BaseRecord {
        int field1;
        std::string field2;
    }
    struct DerivedRecord : public BaseRecord {
        int field3;
        const char* field4;
        std::string field5;
    }
}
"""

class Field(NamedTuple):
    name: str
    type: str

class Record(NamedTuple):
    name: str
    base: "Record"
    fields: list[Field]

class Namespace(NamedTuple):
    name: str
    records: list[Record]

class File(NamedTuple):
    includes: list[str]
    namespaces: list[Namespace]

class ProgramOptions(NamedTuple):
    inputFormat: str
    inputPath: str
    outputPath: str

def parseXml(inputPath : str):
    import xml.etree.ElementTree as ET
    recordsByName = {}
    file = File([], [])
    tree = ET.parse(inputPath)
    root = tree.getroot()
    for i in root.findall("Include"):
        file.includes.append(i.attrib["name"])
    for n in root.findall("Namespace"):
        namespace = Namespace(n.attrib["name"], [])
        for r in n.findall("Record"):
            baseRecord = recordsByName.get(r.get("extends", None), None)
            record = Record(r.attrib["name"], baseRecord, [])
            recordsByName[record.name] = record
            for f in r.findall("Field"):
                record.fields.append(Field(f.attrib["name"], f.attrib["type"]))
            namespace.records.append(record)
        file.namespaces.append(namespace)
    return file


def parseCpp(inputPath : str):
    raise NotImplementedError

def parseInput(inputPath : str, inputFormat : str):
    if (inputFormat == "xml"):
        return parseXml(inputPath)
    else:
        return parseCpp(inputPath)

def getAllFields(record : Record):
    if record is None:
        return []
    if (record.base):
        return getAllFields(record.base) + record.fields
    else:
        return record.fields

def printConstructor(record : Record, out : File):
    allFields = getAllFields(record)
    baseFields = getAllFields(record.base)
    # record(field1:type, field2:type, field3:type) : base(field1, field2), field3(field3) {}
    print(f"    {record.name}(", end="", file=out)
    allFieldsWithType = [f"{f.name}:{f.type}" for f in allFields]
    print(", ".join(allFieldsWithType), end="", file=out)
    print(") : ", end="", file=out)
    baseNames = [f.name for f in baseFields]
    remainingNames = [f.name for f in allFields if f.name not in baseNames]
    if (record.base):
        print(f"{record.base.name}({', '.join(baseNames)})", end="", file=out)
        if (len(remainingNames) > 0):
            print(", ", end="", file=out)
    print(", ".join([f"{n}({n})" for n in remainingNames]), end="", file=out)
    print(" {}", file=out)


def printCpp(parseTree : File, out : File):
    for i in parseTree.includes:
        print(f"#include <{i}>", file=out)
    for n in parseTree.namespaces:
        print(f"namespace {n.name} {{", file=out)
        for r in n.records:
            if (r.base):
                print(f"struct {r.name} : public {r.base.name} {{", file=out)
            else:
                print(f"struct {r.name} {{", file=out)
            for f in r.fields:
                print(f"    {f.type} {f.name};", file=out)
            printConstructor(r, out)
            print("};", file=out)
        print("}", file=out)

def main(options : ProgramOptions):
    parseTree = parseInput(options.inputPath, options.inputFormat)
    printCpp(parseTree, sys.stdout)


if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("-i", "--input", dest="inputPath", help="input file path")
    parser.add_option("-o", "--output", dest="outputPath", help="output file path")
    parser.add_option("-f", "--format", dest="inputFormat", help="input file format")
    parser.set_defaults(inputFormat="xml")
    (options, args) = parser.parse_args()
    main(options)
