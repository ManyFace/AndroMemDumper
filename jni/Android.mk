LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)


LOCAL_MODULE    := dumpMemory
LOCAL_SRC_FILES := dump_memory.c
LOCAL_LDLIBS+= -L$(SYSROOT)/usr/lib -llog
include $(BUILD_EXECUTABLE)
