# Trình diễn hệ thống

Frontend AAPL Forecast Lab bám concept đã chốt,nốiAPI thật,nền sáng/sidebar/history-forecast/cards/journal. Mở localhost5173 khiAPI8000 sẵn sàng. Chi tiết [kịch bản demo](../docs/TV6_Frontend_Demo.md).

1. Data explorer: snapshot/version/adjusted close USD,bảng/biểu đồ phân trang.
2. Origin2025-06-16,H1,seed42,3methods:3dòng,target2025-06-17,actual/error ghép sau.
3. H5 tựbỏCNN,xóaoutputcũ,chạy10dòng LSTM/persistence theo5phiêndataset.
4. Metrics full-split vàselected-range,từngseed/perhorizon/overall,sample/errorcounts vàevaluationphase.
5. Experiment/config/history/audit; lossscaledkhácbiểu diễnkhôngso trực tiếp.
6. Errors phântrang100dòng,sort|error|trongtrang; khônggọi top-toàntập.
7. TraceLSTM verified30bước; gate trungbìnhhidden32khônggiảithíchkinhtế.
8. Journal20requeststhànhcôngtrongtab,khôngphảidựbáođãpháthànhtạingàylịchsử.

5testsJS/14checksChromeAPI thậtđạtởmục9; códesktop/mobile390px/outage. Screenshot vàreceipt theo logs/audit/tv6_item9_latest.json; khôngdùngảnhconcept làmbằngchứngimplementation. Đổi context khônggiữkếtquảcũ,lỗikhôngthay bằngdata giả. Xem [nghiệmthu](audits/TV6_Item9_Frontend.md).
