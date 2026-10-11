#import "common.typ": badge, muted, panel

#let render(data) = panel(
  [Programmes],
  if data.programmes.len() == 0 {
    text(fill: luma(45%), style: "italic")[Aucun programme national recensé.]
  } else {
    for programme in data.programmes [
      #block(below: 0.5em)[
        #badge(programme.nom)
        #if programme.depuis.value != none [
          #h(0.4em) #text(size: 7.5pt, fill: muted)[depuis le #programme.depuis.label]
        ]
      ]
    ]
  },
)
