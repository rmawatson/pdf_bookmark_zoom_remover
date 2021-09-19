from typing import Union
import pikepdf,sys,os,argparse

class data:
    _names = None
    
def update_dest(zoom_factor,current):
    dest = pikepdf.Array()
    dest.append(current[0])
    dest.append(pikepdf.Name("/XYZ"))
    dest.append(0)
    dest.append(0)
    dest.append(zoom_factor)
    dest_type = current[1]
    
    if dest_type == "/XYZ":
        dest[2] = current[2]
        dest[3] = current[3]
    elif dest_type in ("/FitH","/FitBH"):            
        dest[3] = current[2]          
    elif dest_type in ("/FitV","/FitBV"):            
        dest[2] = current[2]          
    elif dest_type == "/FitR":
        dest[2] = current[2]
        dest[3] = current[4]
    #("/Fit","/FitB"):
    
    return dest    
       
def collect_all_names(root):
    if not hasattr(root,"Names"):
        return {}
        
    names = {}

    def _apply_collect_all_names(parent):
        if hasattr(parent,"Kids"):
            for item in parent.Kids:
                _apply_collect_all_names(item)   
        elif hasattr(parent,"Names"):
            for index in range(0,len(parent.Names),2):
                names[parent.Names[index]] = (index+1,parent.Names)
            
    _apply_collect_all_names(root.Names.Dests)
    
    return names
    
def get_names(root):
    if not data._names:
        data._names = collect_all_names(root)
    return data._names

def set_zoom_factor(root,depth,outline_item,zoom_factor,only_bookmarks): 

    skipped = False
    if outline_item.action:
        outline_item.action.D = update_dest(zoom_factor,outline_item.action.D)
    elif outline_item.destination != None:
        if only_bookmarks:
            names = get_names(root)
        if outline_item.destination in names:
            index = names[outline_item.destination][0]
            array = names[outline_item.destination][1]
            array[index] = update_dest(zoom_factor,array[index])
        else:
            raise RuntimeError("Name %s Not Found" % outline_item.destination)
    else:
        skipped = True
        
    print(("skipped" if skipped else "updated") + " >> %s %s" % (" "*depth,outline_item.title))
    
    
def set_all_bookmark_zooms(in_files: Union[str, list[str]],out_file=None,zoom_factor=None,only_bookmarks=False):
    def _apply_set_all_bookmark_zoom(names,depth,children):
        for child in children:
            set_zoom_factor(names,depth,child,zoom_factor,only_bookmarks)
            _apply_set_all_bookmark_zoom(names,depth+1,child.children)

    if isinstance(in_files,str):
        in_files = [in_files]

    for in_file in in_files:
        pdf = pikepdf.open(in_file)
        if not only_bookmarks:
            names = get_names(pdf.Root)
            for values in names.items():
                index,array = values
                array[index] = update_dest(zoom_factor,array[index])

        with pdf.open_outline() as outline:
            _apply_set_all_bookmark_zoom(pdf.Root,0,outline.root)

        save_name = out_file if out_file else in_file.split(".")[0] + "-zoomed.pdf"
        print("saving %s ..." % save_name)
        pdf.save(save_name)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Remove PDF bookmark zooms')
    parser.add_argument('-z','--zoom', type=float,default=None,
                        help='set the zoom factor of the bookmarks/links. 0 will inherit the current zoom (default:0)')
    parser.add_argument('-ob','--only_bookmarks',default=False,action="store_true",
                        help='only process bookmark links, other clickables in the document are left untouched (default:False)')

    parser.add_argument('file_name',nargs='+',help='PDF filename(s) to process')
    parser.add_argument('-o','--out_file',default=None,help='Output filename')
    args = parser.parse_args()
        
    set_all_bookmark_zooms(args.file_name,args.out_file,args.zoom,args.only_bookmarks)    
