BOARD=$(shell basename `pwd`)

LOAD_FILE=/tmp/$(BOARD).load

QUEUE_FILE=/tmp/$(BOARD).queue

TOOL=$(shell find $(HW_DIR)/fpga -name $(BOARD) | cut -d"/" -f7)

JOB=$(shell echo $(USER) `md5sum $(FPGA_OBJ)  | cut -d" " -f1`)

include $(ROOT_DIR)/hardware/hardware.mk

#SOURCES
VSRC+=./verilog/top_system.v

ifeq ($(RUN_EXTMEM),1)
INIT_MEM=0
endif

#console command 
ifeq ($(USE_ETHERNET),)
CONSOLE_CMD=$(PYTHON_DIR)/console -s /dev/usb-uart
else
#Use console ethernet wrapper along python environment with permissions to access ethernet interface
CONSOLE_CMD=source /opt/pyeth3/bin/activate; $(SW_DIR)/python/console_ethernet.py -s /dev/usb-uart -c $(PYTHON_DIR)/console -e $(ETHERNET_DIR) -i $(ETH_IF) -m $(RMAC_ADDR)
endif
ifeq ($(INIT_MEM),0)
CONSOLE_CMD+=-f
endif

#RULES

#
# Use
#

FORCE ?= 1

run:
ifeq ($(NORUN),0)
ifeq ($(BOARD_SERVER),)
	cp $(FIRM_DIR)/firmware.bin .
	if [ ! -f $(LOAD_FILE) ]; then touch $(LOAD_FILE); chown $(USER):dialout $(LOAD_FILE); chmod 664 $(LOAD_FILE); fi;\
	bash -c "trap 'make queue-out' INT TERM KILL; make queue-in; if [ $(FORCE) = 1 -o \"`head -1 $(LOAD_FILE)`\" != \"$(JOB)\" ];\
	then ../prog.sh; echo $(JOB) > $(LOAD_FILE); fi; $(CONSOLE_CMD) $(TEST_LOG); make queue-out;"
else
	ssh $(BOARD_USER)@$(BOARD_SERVER) "if [ ! -d $(REMOTE_ROOT_DIR) ]; then mkdir -p $(REMOTE_ROOT_DIR); fi"
	rsync -avz --delete --force --exclude .git $(ROOT_DIR) $(BOARD_USER)@$(BOARD_SERVER):$(REMOTE_ROOT_DIR) 
	rsync -avz --delete --force --exclude .git $($(UUT_NAME)_DIR) $(BOARD_USER)@$(BOARD_SERVER):$(REMOTE_UUT_DIR)
	bash -c "trap 'make queue-out-remote' INT TERM KILL; ssh $(BOARD_USER)@$(BOARD_SERVER) 'make -C $(REMOTE_ROOT_DIR)/hardware/fpga/$(TOOL)/$(BOARD) $@ INIT_MEM=$(INIT_MEM) FORCE=$(FORCE) TEST_LOG=\"$(TEST_LOG)\"'"
ifneq ($(TEST_LOG),)
	scp $(BOARD_USER)@$(BOARD_SERVER):$(REMOTE_ROOT_DIR)/hardware/fpga/$(TOOL)/$(BOARD)/test.log .
endif
endif
endif

build: $(FPGA_OBJ)

$(FPGA_OBJ): $(wildcard *.sdc) $(VSRC) $(VHDR) $(HEXPROGS) get_vsrc get_vhdr get_tester_defines
ifeq ($(NORUN),0)
ifeq ($(FPGA_SERVER),)
	@rm -f $(FPGA_LOG)
	../build.sh "vhdr" "$(shell cat defines.txt)" "$(wildcard vsrc/*)" "$(DEVICE)"
	make post-build
else
	ssh $(FPGA_USER)@$(FPGA_SERVER) "if [ ! -d $(REMOTE_ROOT_DIR) ]; then mkdir -p $(REMOTE_ROOT_DIR); fi"
	rsync -avz --delete --force --exclude .git $(ROOT_DIR) $(FPGA_USER)@$(FPGA_SERVER):$(REMOTE_ROOT_DIR)
	rsync -avz --delete --force --exclude .git $($(UUT_NAME)_DIR) $(FPGA_USER)@$(FPGA_SERVER):$(REMOTE_UUT_DIR)
	ssh $(FPGA_USER)@$(FPGA_SERVER) 'make -C $(REMOTE_ROOT_DIR)/hardware/fpga/$(TOOL)/$(BOARD) $@ INIT_MEM=$(INIT_MEM) USE_DDR=$(USE_DDR) RUN_EXTMEM=$(RUN_EXTMEM)'
	scp $(FPGA_USER)@$(FPGA_SERVER):$(REMOTE_ROOT_DIR)/hardware/fpga/$(TOOL)/$(BOARD)/$(FPGA_OBJ) .
	scp $(FPGA_USER)@$(FPGA_SERVER):$(REMOTE_ROOT_DIR)/hardware/fpga/$(TOOL)/$(BOARD)/$(FPGA_LOG) .
endif
endif

#
# Board access queue
#
queue-in:
	if [ ! -f $(QUEUE_FILE) ]; then touch $(QUEUE_FILE); chown $(USER):dialout $(QUEUE_FILE); chmod 664 $(QUEUE_FILE); fi;\
	if [ "`head -1 $(QUEUE_FILE)`" != "$(JOB)" ]; then echo $(JOB) >> $(QUEUE_FILE); fi;\
	bash -c "trap 'make queue-out; exit' INT TERM KILL; make queue-wait"

queue-wait:
	while [ "`head -1 $(QUEUE_FILE)`" != "$(JOB)" ]; do echo "Job queued for board access. Queue length: `wc -l $(QUEUE_FILE) | cut -d" " -f1`"; sleep 10s; done

queue-out:
	sed '/$(JOB)/d' $(QUEUE_FILE) > queue; cat queue > $(QUEUE_FILE); rm queue

queue-out-remote:
ifeq ($(BOARD_SERVER),)
	make kill-cnsl
	make queue-out
else
	ssh $(BOARD_USER)@$(BOARD_SERVER) 'make -C $(REMOTE_ROOT_DIR)/hardware/fpga/$(TOOL)/$(BOARD) $@'
endif

#
# Testing
#

test: clean-testlog test1 test2 test3
	diff test.log test.expected

test1:
	make -C $(ROOT_DIR) fpga-clean
	make -C $(ROOT_DIR) fpga-run INIT_MEM=1 USE_DDR=0 RUN_EXTMEM=0 TEST_LOG=">> test.log"

test2:
	make -C $(ROOT_DIR) fpga-clean
	make -C $(ROOT_DIR) fpga-run INIT_MEM=0 USE_DDR=0 RUN_EXTMEM=0 TEST_LOG=">> test.log"

test3:
	make -C $(ROOT_DIR) fpga-clean
	make -C $(ROOT_DIR) fpga-run INIT_MEM=0 USE_DDR=1 RUN_EXTMEM=1 TEST_LOG=">> test.log"


#
# Clean
#

clean-all: hw-clean
	@rm -f $(FPGA_OBJ) $(FPGA_LOG) *.txt
ifneq ($(FPGA_SERVER),)
	ssh $(FPGA_USER)@$(FPGA_SERVER) "if [ ! -d $(REMOTE_ROOT_DIR) ]; then mkdir -p $(REMOTE_ROOT_DIR); fi"
	rsync -avz --delete --force --exclude .git $(ROOT_DIR) $(FPGA_USER)@$(FPGA_SERVER):$(REMOTE_ROOT_DIR)
	rsync -avz --delete --force --exclude .git $($(UUT_NAME)_DIR) $(FPGA_USER)@$(FPGA_SERVER):$(REMOTE_UUT_DIR)
	ssh $(FPGA_USER)@$(FPGA_SERVER) 'make -C $(REMOTE_ROOT_DIR)/hardware/fpga/$(TOOL)/$(BOARD) clean CLEANIP=$(CLEANIP)'
endif
ifneq ($(BOARD_SERVER),)
	ssh $(BOARD_USER)@$(BOARD_SERVER) "if [ ! -d $(REMOTE_ROOT_DIR) ]; then mkdir -p $(REMOTE_ROOT_DIR); fi"
	rsync -avz --delete --force --exclude .git $(ROOT_DIR) $(BOARD_USER)@$(BOARD_SERVER):$(REMOTE_ROOT_DIR)
	rsync -avz --delete --force --exclude .git $($(UUT_NAME)_DIR) $(BOARD_USER)@$(BOARD_SERVER):$(REMOTE_UUT_DIR)
	ssh $(BOARD_USER)@$(BOARD_SERVER) 'make -C $(REMOTE_ROOT_DIR)/hardware/fpga/$(TOOL)/$(BOARD) clean'
endif

#clean test log only when board testing begins
clean-testlog:
	@rm -f test.log
ifneq ($(BOARD_SERVER),)
	ssh $(BOARD_USER)@$(BOARD_SERVER) "if [ ! -d $(REMOTE_ROOT_DIR) ]; then mkdir -p $(REMOTE_ROOT_DIR); fi"
	rsync -avz --delete --force --exclude .git $(ROOT_DIR) $(BOARD_USER)@$(BOARD_SERVER):$(REMOTE_ROOT_DIR)
	rsync -avz --delete --force --exclude .git $($(UUT_NAME)_DIR) $(BOARD_USER)@$(BOARD_SERVER):$(REMOTE_UUT_DIR)
	ssh $(BOARD_USER)@$(BOARD_SERVER) 'make -C $(REMOTE_ROOT_DIR)/hardware/fpga/$(TOOL)/$(BOARD) $@'
endif


.PRECIOUS: $(FPGA_OBJ) test.log

.PHONY: run build \
	queue-in queue-out queue-wait queue-out-remote \
	test test1 test2 test3 \
	clean-all clean-testlog
