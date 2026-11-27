"""Presentation diagrams for TV5. No training or artifact mutation."""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


def _figure(title, subtitle, nodes, edges, size=(15, 10)):
    fig, ax = plt.subplots(figsize=size)
    fig.patch.set_facecolor('#f8fafc')
    ax.set(xlim=(0, 15), ylim=(0, 10))
    ax.axis('off')
    fig.text(.04, .96, title, fontsize=19, fontweight='bold', color='#0f172a')
    fig.text(.04, .925, subtitle, fontsize=11, color='#475569')
    palette = {'data':'#dbeafe','model':'#e0e7ff','check':'#dcfce7',
               'artifact':'#fef3c7','reject':'#fee2e2','note':'#f1f5f9'}
    for key, (x, y, text, kind) in nodes.items():
        ax.add_patch(FancyBboxPatch((x-2.05,y-.52),4.1,1.04,
            boxstyle='round,pad=0.10',facecolor=palette[kind],edgecolor='#94a3b8',linewidth=1.1))
        ax.text(x,y,text,ha='center',va='center',fontsize=11,color='#0f172a',linespacing=1.35)
    for source,target,label in edges:
        x,y,*_ = nodes[source]
        u,v,*_ = nodes[target]
        dx,dy = u-x,v-y
        if abs(dx) > abs(dy):
            start=(x+(2.18 if dx>0 else -2.18),y)
            end=(u-(2.18 if dx>0 else -2.18),v)
        else:
            start=(x,y+(.65 if dy>0 else -.65))
            end=(u,v-(.65 if dy>0 else -.65))
        ax.annotate('',xy=end,xytext=start,
                    arrowprops=dict(arrowstyle='->',color='#334155',lw=1.6))
        if label:
            ax.text((start[0]+end[0])/2+.12,(start[1]+end[1])/2+.10,label,
                    fontsize=9,color='#334155',ha='center',
                    bbox=dict(facecolor='#f8fafc',edgecolor='none',pad=2))
    fig.subplots_adjust(top=.86,bottom=.06,left=.04,right=.96)
    return fig


def render_tv5_diagrams(output_dir):
    """Return four figures plus PNG paths for embedded notebook output."""
    output_dir=Path(output_dir)
    output_dir.mkdir(parents=True,exist_ok=True)
    specs = [
        ('01_data_flow', '1. Dữ liệu TV1 → TV2 → CNN',
         'Luồng đã kiểm local. CNN giữ cùng mẫu/ngày/scaler với LSTM lookback 30 đối ứng.', {
            'a':(3,9,'TV1 · snapshot AAPL\nVersion + 5 source hashes','data'),
            'b':(3,6.8,'TV2 · split theo ngày target\nTrain 2015–2022 / Val 2023','data'),
            'c':(3,4.6,'Scaler chỉ fit train\nDùng lại cho mọi split','check'),
            'd':(3,2.4,'Prepared · cửa sổ 30 phiên\nTarget chung đủ lịch sử 60 phiên','data'),
            'e':(11,2.4,'CNN loader · giữ thứ tự ID/ngày\nTrain 1.954 / Val 250','check'),
            'f':(11,6.8,'CNN chỉ nhận X · (B,30,1)\ny (B,1) chỉ đi vào loss','model'),
            'g':(11,9,'Test 2024–2025\nChưa đo hiệu năng / không tuning','note'),
         }, [('a','b',''),('b','c',''),('c','d',''),('d','e',''),('e','f','CPU float64')]),
        ('02_cnn_shapes', '2. Đường forward bên trong CNN',
         '17.057 tham số. B là số mẫu trong batch, có thể là 1 hoặc batch cuối.', {
            'a':(3,9,'Input X\n(B,30,1)','data'),
            'b':(3,6.8,'Transpose chiều trong model\n(B,1,30)','model'),
            'c':(3,4.6,'Conv1d 1→16 + ReLU\n(B,16,30)','model'),
            'd':(3,2.4,'Conv1d 16→32 + ReLU\n(B,32,30)','model'),
            'e':(11,2.4,'MaxPool1d kernel 2\n(B,32,15)','model'),
            'f':(11,4.6,'Flatten → Dropout 0,1\n(B,480)','model'),
            'g':(11,6.8,'Linear 480→32 + ReLU\n(B,32)','model'),
            'h':(11,9,'Linear 32→1\nDự đoán chuẩn hóa (B,1)','check'),
         }, [('a','b',''),('b','c',''),('c','d',''),('d','e',''),('e','f',''),('f','g',''),('g','h','')]),
        ('03_training_selection', '3. Train, validation và chọn best model',
         'Dùng trainer TV4 chung. Mục 5/6 mới kiểm bằng tensors tổng hợp; chưa train AAPL.', {
            'a':(3,9,'Train loader → model.train()\nDropout hoạt động','data'),
            'b':(3,6.8,'Forward X → prediction\nMSE(prediction, y)','model'),
            'c':(3,4.6,'zero_grad → backward\nKiểm gradient hữu hạn','check'),
            'd':(3,2.4,'Adam step · lr 0,001\nCập nhật trọng số','model'),
            'e':(11,2.4,'Validation · eval + no_grad\nKhông cập nhật trọng số','data'),
            'f':(11,4.6,'Val loss tốt hơn best?\nSo sánh trên validation','check'),
            'g':(11,6.8,'Có → giữ best + gọi saver\nKhông → tăng bộ đếm patience','artifact'),
            'h':(11,9,'Dừng → khôi phục best weights\nPatience hoặc max_epochs','check'),
         }, [('a','b',''),('b','c',''),('c','d','mỗi batch'),('d','e','hết epoch'),
             ('e','f',''),('f','g',''),('g','h','lặp epoch nếu chưa dừng')]),
        ('04_checkpoint', '4. Checkpoint CNN · đường lưu và nạp',
         'Best-model/inference artifact. Chưa chứa Adam/RNG state để resume training.', {
            'a':(3,9,'Saver nhận model + metadata\nTrainer quyết định best epoch','model'),
            'b':(3,6.8,'Kiểm CPU float64 / finite\nConfig + provenance hợp lệ','check'),
            'c':(3,4.6,'Thư mục checkpoint ID mới\nKhông ghi đè run cũ','artifact'),
            'd':(3,2.4,'weights.pt + manifest.json\nChecksum + config fingerprint','artifact'),
            'e':(11,2.4,'Loader đối chiếu expected\nData/scaler/config/run/seed','check'),
            'f':(11,4.6,'Kiểm purpose + weights hash\nSai liên kết/hỏng → từ chối','check'),
            'g':(11,6.8,'weights_only → strict load\nKiểm dtype/finite/shape thật','model'),
            'h':(11,9,'Instance mới · eval()\nDiagnostic cần cho phép rõ ràng','check'),
         }, [('a','b',''),('b','c',''),('c','d',''),('d','e','trusted handoff'),
             ('e','f',''),('f','g',''),('g','h','')]),
    ]
    results=[]
    for name,title,subtitle,nodes,edges in specs:
        fig=_figure(title,subtitle,nodes,edges)
        path=output_dir / (name+'.png')
        fig.savefig(path,dpi=150,facecolor=fig.get_facecolor())
        results.append((fig,path))
    return results
