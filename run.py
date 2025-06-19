from streamlit.web.cli import main

print(f"before main()")  # get printed
main()
print(f"after main()")  # never printed in Ctrl-C
