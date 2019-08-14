import matplotlib.pylab as plt
import numpy as np
import io
import ipywidgets
import base64
import PIL
import PIL.Image
import IPython
import uuid


def save_plot_as_png(**kwargs):
    with io.BytesIO() as output:
        plt.savefig(output,format='png',bbox_inches='tight',**kwargs)
        output.seek(0)
        s=output.read()
    return s



class NumpyMoviesWidget:
    def __init__(self,*movies,width=200):
        self.movies=movies
        self.width=width

    def __call__(self):
        ipywidgets.interact(self.loadimg_html,k=(0,len(self.movies[0].outviz)-1))

    def loadimg_html(self,k):
        s=''

        s="<div style='width:%dpx'>"%(int(self.width*len(self.movies))+5)
        for dm in self.movies:
            s+='<img width="%f" style="display:inline-block;vertical-align:text-bottom;image-rendering: pixelated;" src="data:image/png;base64,%s"> '%(
                    self.width,dm.loadimg_b64(k))

        s+="<br />"

        s+="</div>"

        return IPython.display.HTML(s)

class NumpyMovieWidget:
    def __init__(self,data,colors=None,width=500,norm_per_t=True,cb=None):
        self.width=width

        self.cb=cb

        if not norm_per_t:
            data=np.array(data)
            data=data-data.min()
            data=data/data.max()

        if colors is None:
            colors='b'

        # make colors
        self.colors=np.zeros((len(data),3))
        if isinstance(colors,str):
            colors=[colors]*len(data)
        else:
            colors=list(colors)
        for i,c in enumerate(colors):
            if c=='r':
                self.colors[i]=np.array([4,2,1])
            elif c=='g':
                self.colors[i]=np.array([1,2,.5])
            elif c=='b':
                self.colors[i]=np.array([1,2,4])
            else:
                raise Exception("WTF is %s"%c)

        # make the raw bytes
        self.outviz=[]
        for i,val in enumerate(data):
            if val is not None:
                val=np.require(val)

                if len(val.shape)==3:
                    assert val.dtype==np.uint8
                    self.outviz.append(val)
                else:
                    val=np.require(val,dtype=np.float)
                    assert len(val.shape)==2
                    if norm_per_t:
                        val=val-val.min()
                        val=val/val.max()

                    FM=np.zeros((val.shape[0],val.shape[1],3))
                    FM[:,:,0] = val *self.colors[i,0]
                    FM[:,:,1] = val *self.colors[i,1]
                    FM[:,:,2] = val *self.colors[i,2]
                    FM = np.clip(FM,0,1)

                    FM=np.require(FM*255,dtype=np.uint8)

                    self.outviz.append(FM)
            else:
                self.outviz.append(np.array([[0]],dtype=np.uint8))

    def __call__(self):
        ipywidgets.interact(self.loadimg_html,k=(0,len(self.outviz)-1))

    def loadimg_bytes(self,k):
        with io.BytesIO() as output:
            img=PIL.Image.fromarray(self.outviz[k])
            img.save(output,'png')
            img=output.getvalue()
        return img

    def loadimg_b64(self,k):
        return base64.b64encode(self.loadimg_bytes(k)).decode()

    def loadimg_img(self,k):
        return IPython.display.Image(self.loadimg_bytes(k),width=self.width,height=self.height)

    def loadimg_html(self,k):
        s=''

        if self.cb is not None:
            s+="<h3>"+str(self.cb(k))+"</h3><br />"

        s+='<img width="%f" style="display:inline-block;vertical-align:text-bottom;image-rendering: pixelated;" src="data:image/png;base64,%s"> '%(
                self.width,self.loadimg_b64(k))



        return IPython.display.HTML(s)

class AnimAcross:
    def __init__(self,ratio=.8,sz=4,columns=None):
        self.axes_list=[]
        self.cbs={}
        self.ratio=ratio
        self.sz=sz
        self.columns=columns

    def __enter__(self):
        return self

    def __invert__(self):
        self.axes_list.append(plt.gcf().add_axes([0,0,self.ratio,self.ratio],label="axis%d"%len(self.axes_list)))

    def __neg__(self):
        self.axes_list.append(plt.gcf().add_axes([0,0,self.ratio,self.ratio],label="axis%d"%len(self.axes_list)))
        plt.axis('off')

    def __call__(self,s):
        ~self;
        plt.title(s)

    def cb(self,mappable,idx=None):
        if idx is None:
            idx = len(self.axes_list)-1
        self.cbs[idx] = mappable

    def __exit__(self,exc_type,exc_val,exc_tb):
        if self.columns is None:
            dims=[
                (1,1), # no plots
                (1,1), # 1 plot
                (1,2), # 2 plots
                (1,3), # 3 plots
                (2,2), # 4 plots
                (2,3), # 5 plots
                (2,3), # 6 plots
                (3,3), # 7 plots
                (3,3), # 8 plots
                (3,3), # 9 plots
                (4,4)
            ]
            if len(self.axes_list)<len(dims):
                dims=dims[len(self.axes_list)]
            else:
                cols=int(np.sqrt(len(self.axes_list)))+1
                rows = len(self.axes_list)//cols + 1
                dims=(rows,cols)
        else:
            cols=self.columns
            if len(self.axes_list)%cols==0:
                rows=len(self.axes_list)//cols
            else:
                rows=len(self.axes_list)//cols + 1
            dims=(rows,cols)
            
        plt.gcf().set_size_inches(self.sz,self.sz)
        k=0

        for j in range(dims[0]):
            for i in range(dims[1]):
                if k<len(self.axes_list):
                    self.axes_list[k].set_position((i,dims[1]-j,self.ratio,self.ratio))
                k=k+1

        for i in range(len(self.axes_list)):
            if i in self.cbs:
                plt.colorbar(mappable=self.cbs[i],ax=self.axes_list[i])

        if exc_type is not None:
            print(exc_type,exc_val,exc_tb)




class AnimHere:
    def __init__(self,autorun=True,width=400,height=400,inchwidth=5,dpi=300):
        self.imgs=[]
        self.started=False
        self.autorun=autorun
        self.width=width
        self.height=height
        self.inchwidth=inchwidth
        self.dpi=dpi



    def __enter__(self):
        return self

    def _save(self):
        self.imgs.append(save_plot_as_png(dpi=self.dpi))

    def __invert__(self):
        if self.started:
            self._save()
        else:
            self.started=True
        plt.clf()
        plt.gcf().set_size_inches((self.inchwidth,self.inchwidth*self.height/self.width))

    def __call__(self,s):
        ~self;
        plt.title(s)

    def construct_widget(self):
        slider=ipywidgets.IntSlider(min=0,max=len(self.imgs)-1)
        img=ipywidgets.Image(width=self.width,height=self.height)

        def observer(x):
            spot=x['new']
            img.value=self.imgs[spot]

        slider.observe(observer, names='value')
        img.value=self.imgs[0]

        return ipywidgets.VBox([slider,img])

    def __exit__(self,exc_type,exc_val,exc_tb):
        self._save()
        if exc_type is not None:
            print(exc_type,exc_val,exc_tb)

        plt.clf()
        if self.autorun:
            wid=self.construct_widget()
            IPython.display.display(wid)

    def html_encapsulated(self):
        idx='animac'+str(uuid.uuid1()).replace('-','')
        imgs=[base64.b64encode(x).decode() for x in self.imgs]
        b64s=[('data:image/png;base64,'+imgs[i]) for i in range(len(self.imgs))]
        b64s='["' + '","'.join(b64s) + '"]'

        js=f'''
        <div id="{idx}">
         <input type="range" min=0 max={len(self.imgs)-1} id="{idx}-slider" oninput="{idx}SliderChange();"/>
         <br />
         <img id="{idx}-img" width={self.width} height={self.height}/>
        </div>
        <script type="text/javascript">
        function {idx}SliderChange() {{
            idx = '{idx}'
            b64s={idx}images;
            img=document.getElementById(idx+'-img');
            slider=document.getElementById(idx+'-slider');
            
            img.src = b64s[slider.value%b64s.length];
        }}
        var {idx}images={b64s};
        {idx}SliderChange()
        </script>
        '''
        return js
