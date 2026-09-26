-- GarageBand 10 export automation for Simplified Chinese and English UIs.
-- argv: <preferred output directory, reserved> <filename without extension> <format>

on run argv
	set outName to item 2 of argv
	set fmt to item 3 of argv
	set shareMenus to {"共享", "Share"}
	set exportItems to {"将乐曲导出到磁盘…", "将乐曲导出到磁盘...", "Export Song to Disk…", "Export Song to Disk..."}
	set exportButtons to {"导出", "Export"}
	set replaceButtons to {"替换", "Replace"}

	tell application "GarageBand" to activate
	delay 0.8
	tell application "System Events"
		tell process "GarageBand"
			set clickedExportItem to false
			repeat with menuName in shareMenus
				if clickedExportItem then exit repeat
				try
					set shareMenu to menu 1 of menu bar item (contents of menuName) of menu bar 1
					repeat with itemName in exportItems
						try
							click menu item (contents of itemName) of shareMenu
							set clickedExportItem to true
							exit repeat
						end try
					end repeat
				end try
			end repeat
			if not clickedExportItem then error "GarageBand export menu item not found"

			set exportDialog to missing value
			repeat 40 times
				repeat with candidateWindow in windows
					try
						set candidateGroup to splitter group 1 of candidateWindow
						if exists radio button fmt of candidateGroup then
							set exportDialog to candidateWindow
							exit repeat
						end if
					end try
				end repeat
				if exportDialog is not missing value then exit repeat
				delay 0.25
			end repeat
			if exportDialog is missing value then error "GarageBand export dialog did not appear"

			set exportGroup to splitter group 1 of exportDialog
			try
				set nameField to text field 2 of exportGroup
			on error
				set nameField to first text field of exportGroup
			end try
			set focused of nameField to true
			set value of nameField to outName
			delay 0.2
			click radio button fmt of exportGroup
			delay 0.3

			set clickedExportButton to false
			repeat with buttonName in exportButtons
				try
					click button (contents of buttonName) of exportGroup
					set clickedExportButton to true
					exit repeat
				end try
			end repeat
			if not clickedExportButton then error "GarageBand export button not found"

			delay 1.2
			try
				set replaceSheet to sheet 1 of exportDialog
				repeat with buttonName in replaceButtons
					try
						click button (contents of buttonName) of replaceSheet
						exit repeat
					end try
				end repeat
			end try
		end tell
	end tell
	return "export started"
end run
