# save reqest and response
from burp import IBurpExtender, IContextMenuFactory
from javax.swing import JMenuItem, JFileChooser
from java.util import List, ArrayList
from java.io import File
import os
import re

class BurpExtender(IBurpExtender, IContextMenuFactory):
    
    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        callbacks.setExtensionName("Save Request/Response")
        callbacks.registerContextMenuFactory(self)
        
    def createMenuItems(self, invocation):
        self.context = invocation
        menu_list = ArrayList()
        menu_list.add(JMenuItem("Save Request/Response", actionPerformed=self.saveMessage))
        return menu_list
        
    def get_safe_filename(self, url):
        url = re.sub(r'^https?://', '', url)
        url = url.split('?')[0]
        url = re.sub(r'[<>:"/\\|?*]', '_', url)
        return url
        
    def saveMessage(self, event):
        selected_messages = self.context.getSelectedMessages()
        if selected_messages is None or len(selected_messages) == 0:
            return
            
        chooser = JFileChooser()
        chooser.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY)
        chooser.setDialogTitle("Select directory to save requests/responses")
        ret = chooser.showSaveDialog(None)
        if ret != JFileChooser.APPROVE_OPTION:
            return
            
        output_dir = chooser.getSelectedFile()
        output_path = output_dir.getAbsolutePath()
        
        used_names = set()
        
        for message in selected_messages:
            request = message.getRequest()
            if request is None:
                continue
                
            response = message.getResponse()
            
            request_str = self._helpers.bytesToString(request)
            response_str = self._helpers.bytesToString(response) if response is not None else "No response"
            
            request_info = self._helpers.analyzeRequest(message)
            url = request_info.getUrl().toString()
            
            base_filename = self.get_safe_filename(url)
            filename = base_filename + ".txt"
            
            counter = 1
            while filename in used_names:
                filename = "{0}_{1}.txt".format(base_filename, counter)
                counter += 1
            
            used_names.add(filename)
            file_path = os.path.join(output_path, filename)
            
            try:
                with open(file_path, 'w') as f:
                    f.write("=== REQUEST ===\n")
                    f.write(request_str)
                    f.write("\n\n=== RESPONSE ===\n")
                    f.write(response_str)
            except Exception as e:
                self._callbacks.printError("Error writing to file {0}: {1}".format(file_path, str(e)))
