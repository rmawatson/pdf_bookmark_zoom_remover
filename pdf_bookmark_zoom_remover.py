import pikepdf,sys,os

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
    elif dest_type in ("/FitH","FitBH"):            
        dest[3] = current[2]          
    elif dest_type in ("/FitV","FitBV"):            
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

def set_zoom_factor(root,depth,outline_item,zoom_factor): 

    skipped = False
    if outline_item.action:
        outline_item.action.D = update_dest(zoom_factor,outline_item.action.D)
    elif outline_item.destination != None:
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
    
    
def set_all_bookmark_zooms(in_file,out_file=None,zoom_factor=None):

    def _apply_set_all_bookmark_zoom(names,depth,children):
        for child in children:

            set_zoom_factor(names,depth,child,zoom_factor)
            _apply_set_all_bookmark_zoom(names,depth+1,child.children)
    
    pdf = pikepdf.open(in_file)

    with pdf.open_outline() as outline:
        _apply_set_all_bookmark_zoom(pdf.root,0,outline.root)
        
    save_name = out_file if out_file else in_file.split(".")[0] + "-zoomed.pdf"
    print("saving %s ..." % save_name) 
    pdf.save(save_name)

if __name__ == "__main__":

    if not sys.argv[-1].endswith(".pdf"):
        print("Requires <name>.pdf argument")
        sys.exit(0)
        
    if not os.path.exists(sys.argv[-1]):
        print("File '%s' not found" % sys.argv[-1])
        sys.exit(0)
        
    set_all_bookmark_zooms(sys.argv[-1])    