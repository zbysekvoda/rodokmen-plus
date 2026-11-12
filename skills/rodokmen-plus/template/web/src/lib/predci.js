// Jedna definice „kolik předků a generací známe“ pro úvod, /statistiky/ i /predci/.
// Předek = osoba s Kekulého číslem k > 1 (kořen, tj. výchozí osoba sám sebe nepočítá; k = 1).
// Implex: osoba ve více větvích má v people jedno k (další v `also`), počítá se jednou.
// Generací = nejvyšší generace mezi předky (rodiče = 1), kořen se nepočítá.
export function pocetPredku(people) {
  const anc = Object.values(people).filter((p) => p.k > 1);
  return {
    predku: new Set(anc.map((p) => p.slug ?? p)).size,
    generaci: anc.reduce((m, p) => Math.max(m, p.gen ?? 0), 0),
  };
}

// Text z web.json s placeholdery {predku}, {generaci}, {osob} → hodnoty spočítané při buildu.
export const doplnPocty = (text, hodnoty) => String(text).replace(/\{(\w+)\}/g, (m, k) => (k in hodnoty ? String(hodnoty[k]) : m));
