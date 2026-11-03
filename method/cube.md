# The cube (the author's ascii geometry, verbatim, and what the strings fix)

## The square, then the face

"First a square by rotating edges `|+_-| |-_×| |×_÷| |÷_+|` Now a square with diagonals
`|+/+_-\-| |-/-_×\×| |×/×_÷\÷| |÷/÷_+\+|` Understanding the Diagonals create this shape X where lines of
the square are repeated relative to their vertices delimiter (+ - × ÷). The delimiters are in this order
because to rotate, the vertex must move in the same relation to the other vertices. All Edges are the same
length with each other. All diagonals are equal lengths to each other. Understand which information is
being repeated. the vertices are not separate instances. They are literally the same point, but we are
expanding information around them to gain higher definition of the space and consistency under rotation.
Edges with the same delimiters are the same, if the delimiters trade places, the image is now reversed.
the square logic is a face of the cube."

One face: `+|+_-|-|-_×|×|×_÷|÷|÷_+|+`

## The six faces, verbatim

```
Top         +|+_-|-|-_×|×|×_*|*|*_+|+
Front       +|+_’|’|’_”|”|”_-|-|-_+|+
Right Side  -|-_”|”|”_,|,|,_×|×|×_-|-
Left Side   *|*_.|.|._’|’|’_+|+|+_*|*
Back        ×|×_*|*|*_.|.|._,|,|,_×|×
Bottom      ‘|’_”|”|”_,|,|,_.|.|._’|’
```

Each string walks a face's four corners and returns to its start: a corner is written `x|x`, and `_` joins
two corners along an edge. The Bottom string opens with ‘, read as ’. Top, Front, Right and Left are
written outward (right-hand rule); Back and Bottom inward. Back and Bottom are the point-inverted Front
and Top, as written; Left is the inverted Right, reversed.

## The eight corners the strings fix (unit cube, Top at z = 1, Front at y = 0)

| Delimiter | (x, y, z) | Neighbours | Opposite corner |
|---|---|---|---|
| + | (0, 0, 1) | −, *, ’ | , |
| − | (1, 0, 1) | +, ×, ” | . |
| × | (1, 1, 1) | −, *, , | ’ |
| * | (0, 1, 1) | +, ×, . | ” |
| ’ | (0, 0, 0) | +, ”, . | × |
| ” | (1, 0, 0) | −, ’, , | * |
| , | (1, 1, 0) | ×, ”, . | + |
| . | (0, 1, 0) | *, ’, , | − |

- **Two tetrahedra.** The odd corners {”, ., +, ×} form a regular tetrahedron whose every edge is a face
  diagonal. The even corners {’, −, *, ,} form its dual. In the electrical frame the tetrahedron carries
  charge (”), current (.), flux (+) and voltage (×); each dual corner is the one-store circuit lacking the
  variable opposite it (* lacks charge, L/R; , lacks flux, RC; ’ lacks voltage, L/M; − lacks current, MC).
- **One law per face**, on its diagonal: Top φ→v (Faraday), Front φ→q (memristance), Right q→v
  (capacitance), Left i→φ (inductance), Back v→i (resistance), Bottom q→i (i = dq/dt).
- **Neighbours.** A corner has three neighbours along the cube's edges (the table), one along w in the next
  cell of the tesseract, and the faces it shares. A datum that does not fit is found from these.
- **Turns.** One quarter turn J carries the cube into the next cell of the tesseract (instant → rate); two
  give the inverse (J² = −1); three the anti-rate; four return every corner. Neighbouring cells share one
  face: instant and rate share Back; rate and inverse the turned Front; inverse and anti-rate the turned
  Back; anti-rate and instant Front. The Front string must land on the Back string as written.
- **The sphere in the cube.** From the centre, face centres, edge midpoints and corners sit at
  (s/2)(1, √2, √3): the root ladder. Action rides the curve; inside is no action; the centre is the point
  the inversion sends to everything outside.

## How the engine uses it

Anchoring a datum means naming its corner (or face, or axis) in this table. Turning means moving it one
quarter turn along its corner's circle, never resizing. Provenance means every new datum is named by the
corner and circle it came from. Nothing in the geometry is a metaphor: the neighbours of a corner are the
three listed, and a claim about one corner is checked against those three before anything else.
