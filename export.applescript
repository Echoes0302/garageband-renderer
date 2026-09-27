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
			-- GarageBand may enable the metronome by default, and its click is included
			-- in exported audio. Find the control by accessibility text and turn it off.
			set metronomeControl to missing value
			try
				repeat with candidateCheckbox in (checkboxes of group 1 of window 1)
					set metronomeText to ""
					try
						set metronomeText to metronomeText & " " & (help of candidateCheckbox as text)
					end try
					try
						set metronomeText to metronomeText & " " & (description of candidateCheckbox as text)
					end try
					try
						set metronomeText to metronomeText & " " & (name of candidateCheckbox as text)
					end try
					if metronomeText contains "节拍器" or metronomeText contains "Metronome" or metronomeText contains "metronome" then
						set metronomeControl to candidateCheckbox
						exit repeat
					end if
				end repeat
			end try
			if metronomeControl is missing value then error "GarageBand metronome control not found"
			if (value of metronomeControl) is 1 then click metronomeControl
			delay 0.3

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
