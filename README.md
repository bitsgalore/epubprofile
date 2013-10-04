# Epubprofile
Johan van der Knijff, KB/National Library of the Netherlands.

## What is *epubprofile*?
*Epubprofile* is a simple experimental tool for automated profiling of *epub* files. It wraps around [*epubcheck*](http://code.google.com/p/epubcheck/), which is used for validating each *epub* and for extracting its properties. The *epubcheck* output is then validated against a  [*Schematron*](http://en.wikipedia.org/wiki/Schematron) schema that contains rules (e.g. *epub*s must be well-formed, they must not be encrypted, etc.). This is done through the [*Probatron4J*](http://www.probatron.org/) validator, which is wrapped inside *epubprofile* as well.

Note that is *not* a production-ready tool. I mainly wrote *epubprofile* with the following two purposes in mind:

- Facilitate the analysis of test datasets with *epub* files that are sent to me from time to time;
- Demonstrate (and experiment with) the use of *Schematron* rules to assess *epub* publications against user-defined rules/policies. 

## Dependencies
*Epubprofile* was tested with Python 2.7; Python 3 doesn't seem to work yet. You will also need *Java* 5 or more recent for running *epubcheck* and *Probatron4J* (this is based on *Probatron4J*'s documentation. Some tests indicate possible misbehaviour under *Java* 5;  *Java* 6 appears to work fine.) All other dependencies (*epubcheck*, *Probatron4J* are included with *epubprofile*. 

The *epubcheck* *JAR* and source can be found here:

[http://code.google.com/p/epubcheck/downloads/list](http://code.google.com/p/epubcheck/downloads/list)

The *Probatron* *JAR* file was taken from:

[http://www.probatron.org/probatron4j.html](ttp://www.probatron.org/probatron4j.html)

*Probatron4J*'s source code is available here:

[http://code.google.com/p/probatron4j/source/browse/#svn/trunk/](http://code.google.com/p/probatron4j/source/browse/#svn/trunk/)

## Licensing
*Jprofile* is released under the [Apache 2.0 License](http://www.apache.org/licenses/LICENSE-2.0). *Epubcheck* is released under a [new BSD license](http://opensource.org/licenses/BSD-3-Clause). [*Probatron*](http://www.probatron.org/) is released under the [GNU Affero 3.0 license](http://www.gnu.org/licenses/agpl-3.0.html).

## Configuration
After installing *epubprofile* open *config.xml* and update the *java* path.
<!--
Just unzip the contents of *jprofile_x.y.z_win32.zip* to any empty directory. Then open the configuration file ('*config.xml*') in a text editor and update the value of *java* to the location of *java* on your PC if needed.
-->

## Command-line syntax

    usage: epubprofile.py batchDir outDir schema

## Positional arguments

**batchDir**: directory that contains *epub* files to be analysed  
**outDir**: directory where all output is written
**schema**: name of schema with Schematron rules against which the *epubcheck* output is validated 

## Schemas
The quality assessment is based on a number of rules/tests that are defined a set of *Schematron* schemas. The *schemas* folder in the installation directory contains an example. In principe *any* property that is reported by *epubcheck* can be used here, and new tests can be added by editing the schemas.   
 
###Available schemas
| Name|Description|
| ------| -----:|
| minimal.sch|Minimal schema that requires that *epubs* are well-formed without any encryption|


## Usage examples

###Analyse directory
    epubprofile.py E:\epubtest\test out_test  F:\johan\pythonCode\epubprofile\schemas\minimal.sch

This will analyse all *.epub* files in directory *E:\epubtest\test*. The following output is written to directory *out_test*:

- `epubprofile_status.csv` (status output file)
- `epubprofile_details.txt` (detailed output with specific errors and warnings that were eported by *epubcheck*)
-  *epubcheck* output for each analysed file (*xml*, following the *jhove* schema).

## Status output file
This is a comma-separated file with the assessment status of each analysed file. The assessment status is either *pass* (passed all tests) or *fail* (failed one or more tests). Here's an example:


    E:\epubtest\test\hindawi_article.epub,fail
    E:\epubtest\test\IGPN-0000010554-Right_Ho_Jeeves.epub,pass
    E:\epubtest\test\moby-dick-mo-20120214.epub,pass
    E:\epubtest\test\wasteland-otf-obf-20120118.epub,fail
    E:\epubtest\test\wasteland-woff-20120118.epub,pass
    E:\epubtest\test\wasteland-woff-obf-20120118.epub,fail


## Details output file
This shows the details results of the assessment. An example:

    file name: E:\epubtest\test\moby-dick-mo-20120214.epub
    epub version: 3.0
    schema: file:///F:\johan\pythonCode\epubprofile\schemas\minimal.sch
    validation status: Well-formed
    ####
    file name: E:\epubtest\test\wasteland-otf-obf-20120118.epub
    epub version: 3.0
    schema: file:///F:\johan\pythonCode\epubprofile\schemas\minimal.sch
    validation status: Well-formed
    *** Schema validation errors:
    Test "(jh:name = 'hasEncryption' and jh:values/jh:value ='false') or (jh:name != 'hasEncryption')" failed (Encryption detected)
    ####
    file name: E:\epubtest\test\regime-anticancer-arabic-20120426.epub
    epub version: 3.0
    schema: file:///F:\johan\pythonCode\epubprofile\schemas\minimal.sch
    validation status: Not well-formed
    *** Schema validation errors:
    Test "jh:status = 'Well-formed'" failed (not well-formed epub)
    *** Epubcheck validation errors and warnings:
    WARN: /EPUB/Navigation/toc.ncx: meta@dtb:uid content 'c611a635-d1ec-f6c9-28c1-6c08f20c9f36' should conform to unique-identifier in content.opf: 'code.google.com.epub-samples.regime-anticancer-arabic'
    ERROR: /EPUB/Navigation/toc.ncx: External DTD entities are not allowed. Remove the DOCTYPE.
    ERROR: /EPUB/Navigation/toc.ncx: External DTD entities are not allowed. Remove the DOCTYPE.


In this example, the first *epub* passes all tests. The second one is well-formed, but it doesn't pas the schema validation because it uses encryption. The third *epub* is not well-formed, and the corresponding warnings and errors from *epubcheck*'s output are included.

## Preconditions
- All files that are to be analysed have an *.epub* extension (everything else is ignored!)


##Known limitations
- *epubprofile* currently only runs under Windows (there's a hack to make the schema definition work with Probatron that will *definitely* not work under Linux!
- Recursive scanning of directory trees not supported
- Code is currently not compatible with *Python 3* (tested under *Python 2.7*)
- Files that have names containing square brackets ("[" and "]" are ignored (limitation of *Python*'s *glob* module, will be solved in the future).
- Reference to *epubcheck* JAR hard-coded (will probably move this to config file)
- There will probably be bugs as I threw this together pretty quickly without much testing ... be warned!

##Useful links
- [*epubcheck*](http://code.google.com/p/epubcheck/)
- [*Schematron*](http://en.wikipedia.org/wiki/Schematron)
- [*Probatron*](http://www.probatron.org/)
- [Automated assesment of JP2 against a technical profile using jpylyzer and Schematron](http://www.openplanetsfoundation.org/blogs/2012-09-04-automated-assessment-jp2-against-technical-profile) - describes a similar approach for assessing *JP2* images


