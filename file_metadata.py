import sublime, sublime_plugin
import os
import datetime
import zipfile

# Get platform version
STPlatform = sublime.platform()

### ----------------------------------------------------------------------------

# Get installed build version
STVersion = int( sublime.version() )

# Check if plugin available for use
ST3 = STVersion >= 3000

# Warn if not using ST3 and bounce out (uninstall plugin)
# # TODO: do we need to bounce out and disable the plugin? ...until we implement ST2 compatibility
if not ST3:

    # Display message
    sublime.error_message( 'Sorry! File Metadata package is for use with Sublime Text 3+, it will not work for your installed build ( v.' + str( STVersion )  + '). You should upgrade: http://www.sublimetext.com/3 :)' )


### ----------------------------------------------------------------------------


# TODO: get this working to provide user with options
# Load plugin settings
pluginSettings = sublime.load_settings("FileMetadata.sublime-settings")


### ----------------------------------------------------------------------------


# Copy file metadata to clipboard
class CopyFileMetadataCommand( sublime_plugin.TextCommand ):

    # Initialize; args: meta = type of file info to extract; defaults to 'file_name'; descriptor = description of function being performed
    def run( self, edit, descriptor, meta = 'file_name' ):

            # Get file information
            fileInfo = self.view.file_name()

            # Extract file metadata
            metadata = self.extract_file_metadata( meta, fileInfo )

            # Action!
            self.action( descriptor, metadata )


    def action( self, descriptor, metadata ):

            # Check for errors
            if metadata == 'error':

                # Display error message in status bar
                sublime.status_message( "File hasn't been saved to filesystem or doesn't exist!" )

                # Show error dialog
                sublime.error_message( "File hasn't been saved to filesystem or doesn't exist!" )

            # Check for unsaved changes; NOTE: this check will fail if ""save_on_focus_lost" is set to true in Preferences; TODO consider removing error dialog and just leave status bar message or figure out how to keep file in a 'dirty' state
            elif metadata == 'dirty':

                # Display error message in status bar
                sublime.status_message( "File has unsaved changes! Please save the file then check again" )

                # Show error dialog
                sublime.error_message( "File has unsaved changes! Please save the then check again" )

            else:
                # Display message in status bar
                sublime.status_message( descriptor + ' copied to clipboard: ' + metadata )

                # Override Default menus
                self.defaultMenuOverrides();

                # Copy to clipboard
                sublime.set_clipboard( metadata )

### TODO: REMOVE
                sublime.message_dialog( metadata )
###REMOVE

            # Could not execute any actions
            return False


    def defaultMenuOverrides( self ):

            ## Let's remove 'Copy File Path' from default menus; we'll add our own
            # Create a 'Default' directory in /Packages/ so we can override the default ST menu; 'Default' will be automagically created if it doesn't already exist
            packages_default_dir = os.path.join( os.path.dirname( sublime.packages_path() ), 'Packages', 'Default' )

            # TODO: implement or remove this
            #if not os.path.exists( packages_default_dir ):
            #    os.mkdir( packages_default_dir )

            # Get ST's Default.sublime-package
            default_sublime_package = os.path.join( os.path.dirname( sublime.executable_path() ), 'Packages', 'Default.sublime-package' )

            # Read archive contents but don't truncate
            archive = open( default_sublime_package, 'rb')

            # Unzip archive
            unzippedArchive = zipfile.ZipFile( archive )

            # Iterate over archive files
            for name in unzippedArchive.namelist():

                # Extract file we need
                unzippedArchive.extract( 'Context.sublime-menu', packages_default_dir )

            # Close archive
            unzippedArchive.close()


            ## Edit /Packages/Default/Context.sublime-menu created by File Metadata plugin
            # Retrieve file
            context_sublime_menu = os.path.join( os.path.dirname( sublime.packages_path() ), 'Packages', 'Default', 'Context.sublime-menu' )

            # Open file in 'read' mode
            f = open( context_sublime_menu, 'r' )

            # Get all lines from the file
            lines = f.readlines()

            # Close the file
            f.close()

            # Re-open the file in 'write' mode  (why you need to do dis twice, Python??)
            f = open( context_sublime_menu, 'w' )

            # Iterate over lines
            for line in lines:

                # If line doesn't match our exclude pattern
                if not '{ "command": "copy_path", "caption": "Copy File Path" }' in line:

                    # Write the remaining lines
                    f.write(line)

            # Close the file
            f.close()


    # Extract file metadata
    def extract_file_metadata( self, attribute, fileData = os.getcwd() ):

            # File hasn't been saved to the filesystem, so it won't have a path
            if fileData == None:

                return 'error'

            # File has unsaved changes, so its dirty!
            elif self.view.is_dirty():

                return 'dirty'

            # Let the magic happen...
            else:
                # Make life easier, split file info
                ( basename, ext ) = os.path.splitext( fileData )

                # File path (includes file name and extension)
                if attribute == "file_path":
                    return fileData

                # File name
                elif attribute == "file_name":
                    return os.path.basename( fileData )

                # File name without extension
                elif attribute == "file_name_without_extension":
                    return os.path.basename( basename )

                # Basename of the current file
                elif attribute == "basename":
                    return basename

                # File size
                elif attribute == "file_size_bytes":
                    return str( os.stat( fileData ).st_size ) + ' bytes'

                # File size (kb)
                elif attribute == "file_size_KiB":
                    return str( round( os.stat( fileData ).st_size / 1024, 3 ) ) + ' KiB'

                # File extension
                elif attribute == "file_extension":
                    return ext

                # File extension (no dot)
                elif attribute == "file_extension_no_dot":
                    return ext.strip('.')

                # Parent directory's name
                elif attribute == "parent_dir_name":
                    return os.path.split( os.path.dirname( fileData ) )[1]

                # Parent directory's path, nothing if file has unsaved changes or hasn't been saved to filesystem
                elif attribute == "parent_dir_path":
                    return os.path.abspath( os.path.join( fileData, os.pardir ) )

                # File creation datetime;
                elif attribute == "file_creation_datetime":

                    # FOR MAC or LINUX; TODO: research this further and update accordingly
                        # references:
                            # http://lwn.net/Articles/397442/
                            # https://docs.python.org/2/library/time.html#time.strftime
                            # http://stackoverflow.com/questions/946967/get-file-creation-time-with-python-on-mac
                    # import subprocess <-- add to top of file if uncommenting
                    # def get_creation_time(path):
                    #     p = subprocess.Popen(['stat', '-f%B', path],
                    #         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    #     if p.wait():
                    #         raise OSError(p.stderr.read().rstrip())
                    #     else:
                    #         return int(p.stdout.read())

                    # Check platform
                    if STPlatform == "osx":
                        #  stat() calls on BSD  systems return 'st_birthtime'
                        return str( datetime.datetime.fromtimestamp( os.stat( fileData ).st_birthtime ) ).strftime( '%Y-%m-%d %H:%M:%S' )
                    elif STPlatform == "linux":
                        return str( datetime.datetime.fromtimestamp( os.stat( fileData ).st_birthtime ) ).strftime( '%Y-%m-%d %H:%M:%S' )
                    elif STPlatform == "windows":
                        return str( datetime.datetime.fromtimestamp( os.path.getctime( fileData ) ).strftime( '%Y-%m-%d %H:%M:%S' ) )

                # File creation datetime (locale)
                elif attribute == "file_creation_datetime_locale":
                    return str( datetime.datetime.fromtimestamp( os.path.getctime( fileData ) ).strftime( '%c' ) )

                # File creation datetime (locale, 12H)
                elif attribute == "file_creation_datetime_locale_12h":
                    return str( datetime.datetime.fromtimestamp( os.path.getctime( fileData ) ).strftime( '%x %I:%M:%S %p' ) )

                # File creation date
                elif attribute == "file_creation_date":
                    return str( datetime.datetime.fromtimestamp( os.path.getctime( fileData ) ).strftime( '%Y-%m-%d' ) )

                # File creation date (locale)
                elif attribute == "file_creation_date_locale":
                    return str( datetime.datetime.fromtimestamp( os.path.getctime( fileData ) ).strftime( '%x' ) )

                # File creation time
                elif attribute == "file_creation_time":
                    return str( datetime.datetime.fromtimestamp( os.path.getctime( fileData ) ).strftime( '%H:%M:%S' ) )

                # File creation time (12H)
                elif attribute == "file_creation_time_12h":
                    return str( datetime.datetime.fromtimestamp( os.path.getctime( fileData ) ).strftime( '%I:%M:%S %p' ) )

                # File creation time (locale) TODO: what does this look like in situ?; find remote machine to test this
#                elif attribute == "file_creation_time_locale":
#                    return str( datetime.datetime.fromtimestamp( os.path.getctime( fileData ) ).strftime( '%X' ) )

                # File last modify datetime
                elif attribute == "file_last_modify_datetime":
                    return str( datetime.datetime.fromtimestamp( os.path.getmtime( fileData ) ).strftime( '%Y-%m-%d %H:%M:%S' ) )

                # File last modify datetime (locale)
                elif attribute == "file_last_modify_datetime_locale":
                    return str( datetime.datetime.fromtimestamp( os.path.getmtime( fileData ) ).strftime( '%c' ) )

                # File last modify datetime (locale, 12H)
                elif attribute == "file_last_modify_datetime_locale_12h":
                    return str( datetime.datetime.fromtimestamp( os.path.getmtime( fileData ) ).strftime( '%x %I:%M:%S %p' ) )

                # File last modify date
                elif attribute == "file_last_modify_date":
                    return str( datetime.datetime.fromtimestamp( os.path.getmtime( fileData ) ).strftime( '%Y-%m-%d' ) )

                # File last modify date (locale)
                elif attribute == "file_last_modify_date_locale":
                    return str( datetime.datetime.fromtimestamp( os.path.getmtime( fileData ) ).strftime( '%x' ) )

                # File last modify time
                elif attribute == "file_last_modify_time":
                    return str( datetime.datetime.fromtimestamp( os.path.getmtime( fileData ) ).strftime( '%H:%M:%S' ) )

                # File last modify time (12H)
                elif attribute == "file_last_modify_time_12h":
                    return str( datetime.datetime.fromtimestamp( os.path.getmtime( fileData ) ).strftime( '%I:%M:%S %p' ) )

            # Couldn't find what user was looking for
            return False
