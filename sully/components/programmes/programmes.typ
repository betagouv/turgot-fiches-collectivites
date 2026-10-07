#import "common.typ": badge, muted, panel

#let render(data) = panel(
  [Programmes],
  if data.len() == 0 {
    text(fill: luma(45%), style: "italic")[Aucun programme national recensé.]
  } else {
    for p in data [
      #block(below: 0.5em)[
        #badge(p.at(0))
        #if p.at(1) != "" [
          #h(0.4em) #text(size: 7.5pt, fill: muted)[depuis le #p.at(1)]
        ]
      ]
    ]
  },
)
