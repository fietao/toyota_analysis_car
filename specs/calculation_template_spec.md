# Calculation Template Spec
IMPLEMENTATION NOTE: Read this spec completely before writing any code. After each section is implemented, tick the verification check for that section.

**Source Workbook**: `202605_รถใหม่_ยี่ห้อรถ-ชนิดเชื้อเพลิง-จังหวัด ปี 2564 - พฤษภาคม 2569(calculation).xlsx`

## Sheet: 1.Reg by Powertrain

### Layout & Headers
```text
Row 1: Registration by Powertrain
Row 3: ประเภทรถ : รย.1,2,3,6,9,10,11
Row 5: Powertrain | 2568 | 2569
Row 6: May | Jan-May | 2568 Total | Jan | Feb | Mar | Apr | May | 2569 Total
Row 7: มกราคม | กุมภาพันธ์ | มีนาคม | เมษายน | Units | Share | Units | Share | มิถุนายน | กรกฎาคม | สิงหาคม | กันยายน | ตุลาคม | พฤศจิกายน | ธันวาคม | Units | Share | Units | Units | Units | Units | Units | Share | Growth vs Apr 2569 | Growth vs May 2568 | Units | Share | Growth
Row 8: Grand Total | 64459 | 49319 | 53564 | 47083 | 55572 | =F8/F$8 | =SUM(B8:F8) | =H8/H$8 | 54371 | 51392 | 47293 | 49084 | 46691 | 44206 | 42700 | 605734 | =Q8/Q$8 | 92503 | 48934 | 59596 | 49107 | 61830 | =W8/W$8 | =(W8-V8)/V8 | =(W8-F8)/F8 | 311970 | =AA8/AA$8 | =(AA8-H8)/H8
Row 9: ICE | 37543 | 31172 | 31259 | 27181 | 29136 | =F9/F$8 | =SUM(B9:F9) | =H9/H$8 | 28040 | 28299 | 25870 | 26359 | 23084 | 21732 | 19028 | 328703 | =Q9/Q$8 | 31142 | 28511 | 32171 | 25140 | 25919 | =W9/W$8 | =(W9-V9)/V9 | =(W9-F9)/F9 | 142883 | =AA9/AA$8 | =(AA9-H9)/H9
Row 10: BEV | 12416 | 5162 | 7836 | 6273 | 12046 | =F10/F$8 | =SUM(B10:F10) | =H10/H$8 | 13477 | 10247 | 9850 | 9805 | 10182 | 10674 | 14591 | 122559 | =Q10/Q$8 | 42209 | 4830 | 10130 | 10030 | 18372 | =W10/W$8 | =(W10-V10)/V10 | =(W10-F10)/F10 | 85571 | =AA10/AA$8 | =(AA10-H10)/H10
```

### Formulas
- Cell G8: `=F8/F$8`
- Cell H8: `=SUM(B8:F8)`
- Cell I8: `=H8/H$8`
- Cell R8: `=Q8/Q$8`
- Cell X8: `=W8/W$8`
- Cell Y8: `=(W8-V8)/V8`
- Cell Z8: `=(W8-F8)/F8`
- Cell AB8: `=AA8/AA$8`
- Cell AC8: `=(AA8-H8)/H8`
- Cell G9: `=F9/F$8`
- Cell H9: `=SUM(B9:F9)`
- Cell I9: `=H9/H$8`
- Cell R9: `=Q9/Q$8`
- Cell X9: `=W9/W$8`
- Cell Y9: `=(W9-V9)/V9`


## Sheet: 2.Rank by Brand

### Layout & Headers
```text
Row 1: Registration by Brand
Row 3: ประเภทรถ : รย.1,2,3,6,9,10,11 | (Multiple Items)
Row 4: Powertrain : ALL | (All)
Row 7: Brand | 2568 | 2569
Row 8: Jan | Feb | Mar | Apr | May | Jan-May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | 2568 Total | Jan | Feb | Mar | Apr | May | 2569 Total (Jan-May)
Row 9: Units | Units | Units | Units | Units | Share | Units | Share | Units | Units | Units | Units | Units | Units | Units | Units | Share | Units | Units | Units | Units | Units | Share | Diff | Growth vs Apr 2569 | Growth vs May 2568 | Units | Share | Diff
Row 10: Grand Total | 64459 | 49319 | 53564 | 47083 | 55572 | =F10/F$10 | =SUM(B10:F10) | =H10/H$10 | 54371 | 51392 | 47293 | 49084 | 46691 | 44206 | 42700 | 605734 | =Q10/Q$10 | 92503 | 48934 | 59596 | 49107 | 61830 | =W10/W$10 | =IFERROR((W10-V10)/V10,0) | =IFERROR((W10-F10)/F10,0) | 311970 | =AB10/AB$10
Row 11: TOYOTA | 23501 | 20357 | 21337 | 18654 | 20225 | =F11/F$10 | =SUM(B11:F11) | =H11/H$10 | 19539 | 19757 | 17883 | 18533 | 17685 | 15682 | 13884 | 227037 | =Q11/Q$10 | 23592 | 20557 | 24344 | 19230 | 20723 | =W11/W$10 | =X11-G11 | =IFERROR((W11-V11)/V11,0) | =IFERROR((W11-F11)/F11,0) | 108446 | =AB11/AB$10 | =AC11-I11
```

### Formulas
- Cell G10: `=F10/F$10`
- Cell H10: `=SUM(B10:F10)`
- Cell I10: `=H10/H$10`
- Cell R10: `=Q10/Q$10`
- Cell X10: `=W10/W$10`
- Cell Z10: `=IFERROR((W10-V10)/V10,0)`
- Cell AA10: `=IFERROR((W10-F10)/F10,0)`
- Cell AC10: `=AB10/AB$10`
- Cell G11: `=F11/F$10`
- Cell H11: `=SUM(B11:F11)`
- Cell I11: `=H11/H$10`
- Cell R11: `=Q11/Q$10`
- Cell X11: `=W11/W$10`
- Cell Y11: `=X11-G11`
- Cell Z11: `=IFERROR((W11-V11)/V11,0)`


## Sheet: 3.ICE by Brand

### Layout & Headers
```text
Row 1: ICE Registration by Brand
Row 3: ประเภทรถ : รย.1,2,3,6,9,10,11 | (Multiple Items)
Row 4: Powertrain : ICE | ICE
Row 6: Sum of จำนวนรถ | Column Labels
Row 7: ICE | 2568 | 2569
Row 8: Jan | Feb | Mar | Apr | May | Jan-May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | 2568 Total | Jan | Feb | Mar | Apr | May | Jan-May
Row 9: Units | Units | Units | Units | Units | Share | Units | Share | Units | Units | Units | Units | Units | Units | Units | Units | Share | Units | Units | Units | Units | Units | Share | Diff | Growth vs Apr 2569 | Growth vs May 2568 | Units | Share | Diff
Row 10: Grand Total | 37543 | 31172 | 31259 | 27181 | 29136 | =F10/F$10 | =SUM(B10:F10) | =H10/H$10 | 28040 | 28299 | 25870 | 26359 | 23084 | 21732 | 19028 | 328703 | =Q10/Q$10 | 31142 | 28511 | 32171 | 25140 | 25919 | =W10/W$10 | =IFERROR((W10-V10)/V10,0) | =IFERROR((W10-F10)/F10,0) | 142883 | =AB10/AB$10
```

### Formulas
- Cell G10: `=F10/F$10`
- Cell H10: `=SUM(B10:F10)`
- Cell I10: `=H10/H$10`
- Cell R10: `=Q10/Q$10`
- Cell X10: `=W10/W$10`
- Cell Z10: `=IFERROR((W10-V10)/V10,0)`
- Cell AA10: `=IFERROR((W10-F10)/F10,0)`
- Cell AC10: `=AB10/AB$10`
- Cell G11: `=F11/F$10`
- Cell H11: `=SUM(B11:F11)`
- Cell I11: `=H11/H$10`
- Cell R11: `=Q11/Q$10`
- Cell X11: `=W11/W$10`
- Cell Y11: `=X11-G11`
- Cell Z11: `=IFERROR((W11-V11)/V11,0)`


## Sheet: 4.BEV by Brand

### Layout & Headers
```text
Row 1: BEV Registration by Brand
Row 3: ประเภทรถ : รย.1,2,3,6,9,10,11 | (Multiple Items)
Row 4: Powertrain : BEV | BEV
Row 6: Sum of จำนวนรถ | Column Labels
Row 7: BEV | 2568 | 2569
Row 8: Jan | Feb | Mar | Apr | May | Jan-May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | 2568 Total | Jan | Feb | Mar | Apr | May | Jan-May 2569
Row 9: Units | Units | Units | Units | Units | Share | Units | Share | Units | Units | Units | Units | Units | Units | Units | Units | Share | Units | Units | Units | Units | Units | Share | Diff | Growth vs Apr 2569 | Growth vs May 2568 | Units | Share | Diff
Row 10: Grand Total | 12416 | 5162 | 7836 | 6273 | 12046 | =F10/F$10 | =SUM(B10:F10) | =H10/H$10 | 13477 | 10247 | 9850 | 9805 | 10182 | 10674 | 14591 | 122559 | =Q10/Q$10 | 42209 | 4830 | 10130 | 10030 | 18372 | =W10/W$10 | =IFERROR((W10-V10)/V10,0) | =IFERROR((W10-F10)/F10,0) | 85571 | =AB10/AB$10
```

### Formulas
- Cell G10: `=F10/F$10`
- Cell H10: `=SUM(B10:F10)`
- Cell I10: `=H10/H$10`
- Cell R10: `=Q10/Q$10`
- Cell X10: `=W10/W$10`
- Cell Z10: `=IFERROR((W10-V10)/V10,0)`
- Cell AA10: `=IFERROR((W10-F10)/F10,0)`
- Cell AC10: `=AB10/AB$10`
- Cell G11: `=F11/F$10`
- Cell H11: `=SUM(B11:F11)`
- Cell I11: `=H11/H$10`
- Cell R11: `=Q11/Q$10`
- Cell X11: `=W11/W$10`
- Cell Y11: `=X11-G11`
- Cell Z11: `=IFERROR((W11-V11)/V11,0)`


## Sheet: 5.HEV by Brand

### Layout & Headers
```text
Row 1: HEV Registration by Brand
Row 3: ประเภทรถ : รย.1,2,3,6,9,10,11 | (Multiple Items)
Row 4: Powertrain : HEV | HEV
Row 7: HEV | 2568 | 2569
Row 8: Jan | Feb | Mar | Apr | May | Jan-May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | 2568 Total | Jan | Feb | Mar | Apr | May | Jan-May 2569
Row 9: Units | Units | Units | Units | Units | Share | Units | Share | Units | Units | Units | Units | Units | Units | Units | Units | Share | Units | Units | Units | Units | Units | Share | Diff | Growth vs Apr 2569 | Growth vs May 2568 | Units | Share | Diff
Row 10: Grand Total | 13433 | 11972 | 12439 | 10350 | 11995 | =F10/F$10 | =SUM(B10:F10) | =H10/H$10 | 11336 | 11570 | 10536 | 11565 | 11993 | 10733 | 8220 | 136142 | =Q10/Q$10 | 17177 | 14572 | 16123 | 12657 | 15102 | =W10/W$10 | =IFERROR((W10-V10)/V10,0) | =IFERROR((W10-F10)/F10,0) | 75631 | =AB10/AB$10
Row 11: TOYOTA | 7020 | 5730 | 6124 | 5283 | 5913 | =F11/F$10 | =SUM(B11:F11) | =H11/H$10 | 5443 | 5414 | 4861 | 5272 | 5963 | 5272 | 4191 | 66486 | =Q11/Q$10 | 8454 | 6818 | 8048 | 6245 | 7052 | =W11/W$10 | =X11-G11 | =IFERROR((W11-V11)/V11,0) | =IFERROR((W11-F11)/F11,0) | 36617 | =AB11/AB$10 | =AC11-I11
```

### Formulas
- Cell G10: `=F10/F$10`
- Cell H10: `=SUM(B10:F10)`
- Cell I10: `=H10/H$10`
- Cell R10: `=Q10/Q$10`
- Cell X10: `=W10/W$10`
- Cell Z10: `=IFERROR((W10-V10)/V10,0)`
- Cell AA10: `=IFERROR((W10-F10)/F10,0)`
- Cell AC10: `=AB10/AB$10`
- Cell G11: `=F11/F$10`
- Cell H11: `=SUM(B11:F11)`
- Cell I11: `=H11/H$10`
- Cell R11: `=Q11/Q$10`
- Cell X11: `=W11/W$10`
- Cell Y11: `=X11-G11`
- Cell Z11: `=IFERROR((W11-V11)/V11,0)`


## Sheet: 6.PHEV by Brand

### Layout & Headers
```text
Row 1: PHEV Registration by Brand
Row 3: ประเภทรถ : รย.1,2,3,6,9,10,11 | (Multiple Items)
Row 4: Powertrain : PHEV | PHEV
Row 6: Sum of จำนวนรถ | Column Labels
Row 7: PHEV | 2568 | 2569
Row 8: Jan | Feb | Mar | Apr | May | Jan-May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | 2568 Total | Jan | Feb | Mar | Apr | May | Jan-May 2569
Row 9: Units | Units | Units | Units | Units | Share | Units | Share | Units | Units | Units | Units | Units | Units | Units | Units | Share | Units | Units | Units | Units | Units | Share | Diff | Growth vs Apr 2569 | Growth vs May 2568 | Units | Share | Diff
Row 10: Grand Total | 1067 | 1013 | 2030 | 3279 | 2395 | =F10/F$10 | =SUM(B10:F10) | =H10/H$10 | 1518 | 1276 | 1037 | 1355 | 1432 | 1067 | 861 | 18330 | =Q10/Q$10 | 1975 | 1021 | 1172 | 1280 | 2437 | =W10/W$10 | =IFERROR((W10-V10)/V10,0) | =IFERROR((W10-F10)/F10,0) | 7885 | =AB10/AB$10
```

### Formulas
- Cell G10: `=F10/F$10`
- Cell H10: `=SUM(B10:F10)`
- Cell I10: `=H10/H$10`
- Cell R10: `=Q10/Q$10`
- Cell X10: `=W10/W$10`
- Cell Z10: `=IFERROR((W10-V10)/V10,0)`
- Cell AA10: `=IFERROR((W10-F10)/F10,0)`
- Cell AC10: `=AB10/AB$10`
- Cell G11: `=F11/F$10`
- Cell H11: `=SUM(B11:F11)`
- Cell I11: `=H11/H$10`
- Cell R11: `=Q11/Q$10`
- Cell X11: `=W11/W$10`
- Cell Y11: `=X11-G11`
- Cell Z11: `=IFERROR((W11-V11)/V11,0)`


## Sheet: 7.BEV by Model

### Layout & Headers
```text
Row 1: Registration of Major BEV Brand by Model
Row 3: ประเภทรถ : รย.1,2,3,6,9,10,11 | (Multiple Items)
Row 4: Powertrain : BEV (only Major BEV Brand) | BEV Major
Row 6: Brand/Model | 2568 | 2569
Row 7: Jan | Feb | Mar | Apr | May | Jan-May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | 2568 Total | Jan | Feb | Mar | Apr | May | 2569 Total (Jan-May)
Row 8: Units | Units | Units | Units | Units | Share | Share | Units | Units | Units | Units | Units | Units | Units | Units | Share | Units | Units | Units | Units | Units | Share | Dif | Growth vs Apr 2569 | Growth vs May 2568 | Units | Share | Dif
Row 9: Grand Total | 11909 | 4696 | 7382 | 5856 | 11573 | =SUM(B9:F9) | 12997 | 9708 | 9337 | 9294 | 9649 | 10123 | 14283 | 116807 | 41584 | 4331 | 9644 | 9598 | 17755 | =IFERROR((W9-V9)/V9,0) | =IFERROR((W9-F9)/F9,0) | 82912
Row 10: BYD | 4382 | 1121 | 1990 | 2142 | 4225 | =F10/F$9 | =SUM(B10:F10) | =H10/H$9 | 5807 | 2824 | 2223 | 2126 | 1633 | 1944 | 2660 | 33077 | =Q10/Q$9 | 12171 | 86 | 604 | 1389 | 3630 | =W10/W$9 | =X10-G10 | =IFERROR((W10-V10)/V10,0) | =IFERROR((W10-F10)/F10,0) | 17880 | =AB10/AB$9 | =AC10-I10
```

### Formulas
- Cell H9: `=SUM(B9:F9)`
- Cell Z9: `=IFERROR((W9-V9)/V9,0)`
- Cell AA9: `=IFERROR((W9-F9)/F9,0)`
- Cell G10: `=F10/F$9`
- Cell H10: `=SUM(B10:F10)`
- Cell I10: `=H10/H$9`
- Cell R10: `=Q10/Q$9`
- Cell X10: `=W10/W$9`
- Cell Y10: `=X10-G10`
- Cell Z10: `=IFERROR((W10-V10)/V10,0)`
- Cell AA10: `=IFERROR((W10-F10)/F10,0)`
- Cell AC10: `=AB10/AB$9`
- Cell AD10: `=AC10-I10`
- Cell G11: `=F11/F$10`
- Cell H11: `=SUM(B11:F11)`


## Sheet: 8.Rank by BEV Model

### Layout & Headers
```text
Row 1: Ranking of Registration of Major BEV Brand by Model
Row 3: ประเภทรถ : รย.1,2,3,6,9,10,11
Row 4: Powertrain : BEV (only Major BEV Brand)
Row 7: Model | Brand | 2568 | 2569
Row 8: Jan | Feb | Mar | Apr | May | Jan-May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | 2568 Total | Jan | Feb | Mar | Apr | May | Jan-May 2569
Row 9: Units | Units | Units | Units | Units | Share | Units | Share | Units | Units | Units | Units | Units | Units | Units | Units | Share | Units | Units | Units | Units | Units | Share | Diff | Growth vs Apr 2569 | Growth vs May 2568 | Units | Share
Row 10: Grand Total | 11909 | 4696 | 7382 | 5856 | 11573 | =G10/G$10 | =SUM(C10:G10) | =I10/I$10 | 12997 | 9708 | 9337 | 9294 | 9649 | 10123 | 14283 | 116807 | =R10/R$10 | 41584 | 4331 | 9644 | 9598 | 17755 | =X10/X$10 | =IFERROR((X10-W10)/W10,0) | =IFERROR((X10-G10)/G10,0) | 82912 | =AC10/AC$10
Row 11: 5 EV | JAECOO | =G11/G$10 | =SUM(C11:G11) | =I11/I$10 | 1 | 226 | 2001 | 3398 | 5626 | =R11/R$10 | 6806 | 705 | 1183 | 1059 | 1010 | =X11/X$10 | =Y11-H11 | =IFERROR((X11-W11)/W11,0) | =IFERROR((X11-G11)/G11,0) | 10763 | =AC11/AC$10
```

### Formulas
- Cell H10: `=G10/G$10`
- Cell I10: `=SUM(C10:G10)`
- Cell J10: `=I10/I$10`
- Cell S10: `=R10/R$10`
- Cell Y10: `=X10/X$10`
- Cell AA10: `=IFERROR((X10-W10)/W10,0)`
- Cell AB10: `=IFERROR((X10-G10)/G10,0)`
- Cell AD10: `=AC10/AC$10`
- Cell H11: `=G11/G$10`
- Cell I11: `=SUM(C11:G11)`
- Cell J11: `=I11/I$10`
- Cell S11: `=R11/R$10`
- Cell Y11: `=X11/X$10`
- Cell Z11: `=Y11-H11`
- Cell AA11: `=IFERROR((X11-W11)/W11,0)`

