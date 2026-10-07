#import "commun.typ": discret, encadre, etiquette

#let rendu(donnees) = encadre(
  [Programmes],
  if donnees.len() == 0 {
    text(fill: luma(45%), style: "italic")[Aucun programme national recensé.]
  } else {
    for p in donnees [
      #block(below: 0.5em)[
        #etiquette(p.at(0))
        #if p.at(1) != "" [
          #h(0.4em) #text(size: 7.5pt, fill: discret)[depuis le #p.at(1)]
        ]
      ]
    ]
  },
)
