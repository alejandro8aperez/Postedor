; ================================================
; Poste Hexagonal 12m (4 tramos de 3m)
; Autor: Alejandro Ochoa
; Software: NanoCAD / AutoCAD compatible
; Unidad: Milímetros (mm)
; ================================================

(defun c:POSTE12M ( / baseRad alturaTotal numTramos altoTramo i z0 z1 ang puntos hexagono face solid)
  (setq baseRad 170.0)           ; Radio del hexágono = 340mm/2
  (setq alturaTotal 12000.0)     ; Altura total 12 m
  (setq numTramos 4)             ; Cantidad de tramos
  (setq altoTramo (/ alturaTotal numTramos)) ; 3000 mm

  (command "._ucs" "w")          ; UCS mundial

  (defun crearHexagono (r / i ang puntos)
    (setq puntos '())
    (setq i 0)
    (repeat 6
      (setq ang (* i (/ (* 2 pi) 6)))
      (setq puntos (append puntos
        (list (list (* r (cos ang)) (* r (sin ang))) )))
      (setq i (1+ i))
    )
    (command "_.PLINE")
    (foreach p puntos (command p))
    (command "C") ; cerrar
  )

  ; Crear un solo hexágono base
  (crearHexagono baseRad)
  (setq ent (entlast)) ; guarda el hexágono
  (setq z0 0.0)

  (repeat numTramos
    (setq z1 (+ z0 altoTramo))
    (command "_.copy" ent "" '(0 0 0) (list 0 0 z1))
    (setq ent2 (entlast))
    (command "_.region" ent ent2 "")
    (setq region1 (entlast))
    (setq region2 (entnext region1))
    (if (and region1 region2)
      (progn
        (command "_.loft" region1 region2 "" "")
        (setq sol (entlast))
        (command "_.chprop" sol "" "la" (strcat "Tramo_" (itoa (+ 1 (fix (/ z1 altoTramo))))) "")
      )
    )
    (setq z0 z1)
  )

  (princ "\n✅ Poste de 12m (4 tramos de 3m) creado correctamente.")
  (princ)
)
