import { useState } from 'react';
import { FileUpload } from '@/components/FileUpload';
import { ResultsPanel } from '@/components/ResultsPanel';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { FileText, Book, Shield, Loader2 } from 'lucide-react';
import { toast } from '@/hooks/use-toast';
import { loadNamesLibrary, type CzechNamesLibrary } from '@/lib/czechNames';
import { CzechAnonymizer } from '@/lib/anonymizer';
import mammoth from 'mammoth';

const Index = () => {
  const [namesLibrary, setNamesLibrary] = useState<CzechNamesLibrary | null>(null);
  const [document, setDocument] = useState<File | null>(null);
  const [processing, setProcessing] = useState(false);
  const [results, setResults] = useState<{
    anonymizedText: string;
    mapping: Record<string, string[]>;
  } | null>(null);

  const handleLibraryUpload = async (file: File) => {
    try {
      const text = await file.text();
      const data: CzechNamesLibrary = JSON.parse(text);
      setNamesLibrary(data);
      loadNamesLibrary(data);
    } catch (error) {
      toast({
        title: "Chyba",
        description: "Nepodařilo se načíst knihovnu jmen",
        variant: "destructive",
      });
    }
  };

  const handleDocumentUpload = (file: File) => {
    setDocument(file);
    toast({
      title: "Dokument načten",
      description: file.name,
    });
  };

  const processDocument = async () => {
    if (!document || !namesLibrary) {
      toast({
        title: "Chyba",
        description: "Nejprve načtěte knihovnu jmen i dokument",
        variant: "destructive",
      });
      return;
    }

    setProcessing(true);

    try {
      // Read DOCX file
      const arrayBuffer = await document.arrayBuffer();
      const result = await mammoth.extractRawText({ arrayBuffer });
      const text = result.value;

      // Anonymize
      const anonymizer = new CzechAnonymizer();
      const anonymized = anonymizer.anonymize(text);

      setResults(anonymized);
      
      toast({
        title: "Hotovo!",
        description: `Dokument byl úspěšně anonimizován`,
      });
    } catch (error) {
      console.error(error);
      toast({
        title: "Chyba",
        description: "Nepodařilo se zpracovat dokument",
        variant: "destructive",
      });
    } finally {
      setProcessing(false);
    }
  };

  const downloadText = () => {
    if (!results) return;
    
    const blob = new Blob([results.anonymizedText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = window.document.createElement('a');
    link.href = url;
    link.download = document?.name.replace('.docx', '_anon.txt') || 'anonymized.txt';
    link.click();
    URL.revokeObjectURL(url);
  };

  const downloadMapping = () => {
    if (!results) return;
    
    let mapText = '';
    const categories = {
      PERSON: 'OSOBY',
      BANK: 'BANKOVNÍ ÚČTY',
      DATE: 'DATA',
      ADDRESS: 'ADRESY',
    };

    Object.entries(categories).forEach(([key, label]) => {
      const items = Object.entries(results.mapping).filter(([tag]) => 
        tag.includes(key)
      );
      
      if (items.length > 0) {
        mapText += `${label}\n${'-'.repeat(label.length)}\n`;
        items.forEach(([tag, values]) => {
          values.forEach(value => {
            mapText += `${tag}: ${value}\n`;
          });
        });
        mapText += '\n';
      }
    });

    const blob = new Blob([mapText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = window.document.createElement('a');
    link.href = url;
    link.download = document?.name.replace('.docx', '_map.txt') || 'mapping.txt';
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-secondary/20 to-background">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Shield className="w-12 h-12 text-primary" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              Český anonimizátor dokumentů
            </h1>
          </div>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Automatická anonimizace jmen, adres, bankovních účtů a dalších citlivých údajů v českých dokumentech
          </p>
        </div>

        {!results ? (
          <div className="grid lg:grid-cols-2 gap-6 mb-6">
            {/* Library Upload */}
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Book className="w-5 h-5 text-primary" />
                  Knihovna jmen
                </CardTitle>
                <CardDescription>
                  Nahrajte JSON soubor s databází českých jmen (cz_names.v1.json)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <FileUpload
                  onFileSelect={handleLibraryUpload}
                  accept=".json"
                  label={namesLibrary ? '✓ Knihovna načtena' : 'Nahrát knihovnu jmen'}
                  icon={<Book className="w-8 h-8" />}
                />
              </CardContent>
            </Card>

            {/* Document Upload */}
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-primary" />
                  Dokument
                </CardTitle>
                <CardDescription>
                  Nahrajte DOCX dokument k anonimizaci
                </CardDescription>
              </CardHeader>
              <CardContent>
                <FileUpload
                  onFileSelect={handleDocumentUpload}
                  accept=".docx"
                  label={document ? `✓ ${document.name}` : 'Nahrát dokument'}
                  icon={<FileText className="w-8 h-8" />}
                />
              </CardContent>
            </Card>
          </div>
        ) : null}

        {/* Process Button */}
        {!results && (
          <div className="text-center">
            <Button
              onClick={processDocument}
              disabled={!namesLibrary || !document || processing}
              size="lg"
              className="px-8 py-6 text-lg shadow-lg hover:shadow-xl transition-shadow"
            >
              {processing ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Zpracovávám...
                </>
              ) : (
                <>
                  <Shield className="w-5 h-5 mr-2" />
                  Anonimizovat dokument
                </>
              )}
            </Button>
          </div>
        )}

        {/* Results */}
        {results && (
          <div>
            <div className="mb-6 text-center">
              <Button
                onClick={() => {
                  setResults(null);
                  setDocument(null);
                }}
                variant="outline"
              >
                Zpracovat další dokument
              </Button>
            </div>
            <ResultsPanel
              mapping={results.mapping}
              anonymizedText={results.anonymizedText}
              onDownloadText={downloadText}
              onDownloadMapping={downloadMapping}
            />
          </div>
        )}

        {/* Info Footer */}
        {!results && (
          <Card className="mt-12 bg-muted/30 shadow-md">
            <CardHeader>
              <CardTitle className="text-lg">Jak to funguje?</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground">
              <p>
                <strong>1. Knihovna jmen:</strong> Systém porovnává jména v dokumentu s databází českých jmen a detekuje všechny jejich tvary (skloňování).
              </p>
              <p>
                <strong>2. Inteligentní detekce:</strong> Rozpoznává bankovní účty, data narození, adresy a další citlivé údaje.
              </p>
              <p>
                <strong>3. Přesné nahrazení:</strong> Každá entita je nahrazena unikátním tagem (např. [[PERSON_1]], [[BANK_1]]).
              </p>
              <p>
                <strong>4. Kompletní mapa:</strong> Získáte přehled všech detekovaných a nahrazených hodnot.
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default Index;
