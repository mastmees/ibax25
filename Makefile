CXX=g++
LD=ld
OBJCOPY=objcopy
OBJDUMP=objdump
LD=g++

#generic compiler options
CFLAGS=-I. $(INCLUDEDIRS) -g \
	-fpack-struct -fshort-enums -Os	   \
	-funsigned-char -Wall \
	-fno-asynchronous-unwind-tables -fno-rtti \
	-Wno-array-bounds -ffunction-sections -fdata-sections

CXXFLAGS=$(CFLAGS) -fno-exceptions

LDFLAGS=-Wl,-gc-sections

.phony: clean backup all

all:	ibax_test


clean:
	find . -name '*~' -delete
	-rm -rf __pycache__
	-rm *.o
	

backup:	clean
	rm -f ../ibax25_backup.zip
	zip -r ../ibax25_backup.zip *

ibax_test: clean ibax_test.o ibax.hpp ibax_test.cpp
	$(LD) ibax_test.o -o $@
	
%.o : %.cpp
	$(CXX) $(CXXFLAGS) $(INCLUDEDIRS) -c $< -o $@

%.o : %.c
	$(CC) $(CFLAGS) $(INCLUDEDIRS) -c $< -o $@
