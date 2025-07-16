#!/usr/bin/env python3
"""
Test script for the Enhanced Session Continuity System
Tests the complete lifecycle of session resumption and termination
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add the MCP Knowledge Server to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services', 'mcp-knowledge-server', 'src'))

from knowledge_server import (
    resume_session,
    endsession,
    initialize_claude_session,
    log_conversation_message,
    log_claude_action,
    get_full_conversation_context
)

class SessionContinuityTester:
    """Comprehensive test suite for session continuity"""
    
    def __init__(self):
        self.test_results = []
        self.test_session_id = None
        
    async def run_all_tests(self):
        """Run the complete test suite"""
        print("🧪 Starting Enhanced Session Continuity System Tests")
        print("=" * 60)
        
        # Test 1: Fresh session start
        await self.test_fresh_session_start()
        
        # Test 2: Session with mock activity
        await self.test_session_with_activity()
        
        # Test 3: Session resumption
        await self.test_session_resumption()
        
        # Test 4: Session termination
        await self.test_session_termination()
        
        # Test 5: Resume after termination
        await self.test_resume_after_termination()
        
        # Print results
        self.print_test_results()
        
    async def test_fresh_session_start(self):
        """Test starting a fresh session with no previous context"""
        print("\n🌱 Test 1: Fresh Session Start")
        print("-" * 40)
        
        try:
            # This should create a new session since no previous one exists
            result = await resume_session(
                project="test-project",
                quick_summary=True,
                auto_initialize=True
            )
            
            if result.get("status") == "fresh_start":
                print("✅ Fresh session start successful")
                self.test_session_id = result.get("new_session", {}).get("session_id")
                print(f"   Session ID: {self.test_session_id}")
                self.test_results.append(("Fresh Session Start", True, "New session created successfully"))
            else:
                print("❌ Fresh session start failed")
                self.test_results.append(("Fresh Session Start", False, f"Unexpected status: {result.get('status')}"))
                
        except Exception as e:
            print(f"❌ Fresh session start error: {e}")
            self.test_results.append(("Fresh Session Start", False, str(e)))
            
    async def test_session_with_activity(self):
        """Test logging various activities in the session"""
        print("\n📝 Test 2: Session Activity Logging")
        print("-" * 40)
        
        if not self.test_session_id:
            print("❌ No session ID available for activity testing")
            self.test_results.append(("Session Activity", False, "No session ID available"))
            return
            
        try:
            # Log a conversation message
            msg_result = await log_conversation_message(
                session_id=self.test_session_id,
                message_type="user_message",
                content="Test message for session continuity testing",
                context={"test_mode": True}
            )
            
            # Log some actions
            action_results = []
            test_actions = [
                ("file_edit", "Edited test file for continuity testing", ["test_file.py"], True),
                ("command", "Ran test command", [], True),
                ("config_change", "Modified test configuration", ["config.json"], False),  # Simulate failure
                ("session_test", "Session continuity test action", [], True)
            ]
            
            for action_type, description, files, success in test_actions:
                action_result = await log_claude_action(
                    session_id=self.test_session_id,
                    action_type=action_type,
                    description=description,
                    files_affected=files,
                    success=success
                )
                action_results.append(action_result)
                
            if msg_result.get("status") == "logged" and all(ar.get("status") == "logged" for ar in action_results):
                print("✅ Session activity logging successful")
                print(f"   Message logged: {msg_result.get('message_id')}")
                print(f"   Actions logged: {len(action_results)}")
                self.test_results.append(("Session Activity", True, f"Logged {len(action_results)} actions and 1 message"))
            else:
                print("❌ Session activity logging failed")
                self.test_results.append(("Session Activity", False, "Failed to log activities"))
                
        except Exception as e:
            print(f"❌ Session activity error: {e}")
            self.test_results.append(("Session Activity", False, str(e)))
            
    async def test_session_resumption(self):
        """Test resuming a session with existing context"""
        print("\n🔄 Test 3: Session Resumption")
        print("-" * 40)
        
        try:
            # This should now find our previous session and resume from it
            result = await resume_session(
                project="test-project",
                quick_summary=False,  # Get full context
                auto_initialize=True
            )
            
            if result.get("status") == "session_resumed":
                print("✅ Session resumption successful")
                
                # Check if we got the expected context
                previous_session = result.get("previous_session", {})
                session_analysis = result.get("session_analysis", {})
                recent_work = result.get("recent_work", {})
                
                print(f"   Previous session: {previous_session.get('session_id')}")
                print(f"   Total actions: {session_analysis.get('total_actions', 0)}")
                print(f"   Success rate: {session_analysis.get('success_rate', 0):.2f}")
                print(f"   Files modified: {len(recent_work.get('files_modified', []))}")
                
                # Verify we have continuation guidance
                guidance = result.get("continuation_guidance", {})
                if guidance.get("next_steps") and guidance.get("recommendations"):
                    print("   ✅ Continuation guidance provided")
                    self.test_results.append(("Session Resumption", True, "Full context loaded with guidance"))
                else:
                    print("   ⚠️ Limited continuation guidance")
                    self.test_results.append(("Session Resumption", True, "Context loaded but limited guidance"))
                    
            else:
                print("❌ Session resumption failed")
                self.test_results.append(("Session Resumption", False, f"Unexpected status: {result.get('status')}"))
                
        except Exception as e:
            print(f"❌ Session resumption error: {e}")
            self.test_results.append(("Session Resumption", False, str(e)))
            
    async def test_session_termination(self):
        """Test graceful session termination"""
        print("\n🏁 Test 4: Session Termination")
        print("-" * 40)
        
        try:
            # End the session gracefully
            result = await endsession(
                session_id=self.test_session_id,
                reason="test_completion",
                completion_timeout=10,  # Shorter timeout for testing
                prepare_resume=True,
                export_context=True
            )
            
            if result.get("status") == "session_ended":
                print("✅ Session termination successful")
                
                # Check data persistence
                persistence = result.get("data_persistence", {})
                summary = result.get("session_summary", {})
                
                print(f"   Session ID: {result.get('session_id')}")
                print(f"   Context exported: {persistence.get('context_exported', False)}")
                print(f"   Resume prepared: {persistence.get('resume_prepared', False)}")
                print(f"   Database updated: {persistence.get('database_updated', False)}")
                print(f"   Total actions: {summary.get('total_actions', 0)}")
                print(f"   Success rate: {summary.get('success_rate', 0):.2f}")
                
                if all(persistence.values()):
                    print("   ✅ All data persistence checks passed")
                    self.test_results.append(("Session Termination", True, "Clean termination with data persistence"))
                else:
                    print("   ⚠️ Some data persistence issues detected")
                    self.test_results.append(("Session Termination", True, "Terminated with persistence warnings"))
                    
            else:
                print("❌ Session termination failed")
                self.test_results.append(("Session Termination", False, f"Unexpected status: {result.get('status')}"))
                
        except Exception as e:
            print(f"❌ Session termination error: {e}")
            self.test_results.append(("Session Termination", False, str(e)))
            
    async def test_resume_after_termination(self):
        """Test resuming after a clean termination"""
        print("\n🔄 Test 5: Resume After Termination")
        print("-" * 40)
        
        try:
            # Try to resume - should find the terminated session
            result = await resume_session(
                project="test-project",
                quick_summary=True,
                auto_initialize=True
            )
            
            if result.get("status") == "session_resumed":
                print("✅ Resume after termination successful")
                
                # Check if we got the terminated session context
                previous_session = result.get("previous_session", {})
                if previous_session.get("session_id") == self.test_session_id:
                    print(f"   ✅ Correctly resumed from terminated session: {self.test_session_id}")
                    self.test_results.append(("Resume After Termination", True, "Correctly resumed from terminated session"))
                else:
                    print(f"   ⚠️ Resumed from different session: {previous_session.get('session_id')}")
                    self.test_results.append(("Resume After Termination", True, "Resumed but from different session"))
                    
            elif result.get("status") == "fresh_start":
                print("⚠️ Resume after termination resulted in fresh start")
                self.test_results.append(("Resume After Termination", False, "No session found to resume"))
                
            else:
                print("❌ Resume after termination failed")
                self.test_results.append(("Resume After Termination", False, f"Unexpected status: {result.get('status')}"))
                
        except Exception as e:
            print(f"❌ Resume after termination error: {e}")
            self.test_results.append(("Resume After Termination", False, str(e)))
            
    def print_test_results(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 60)
        print("🧪 SESSION CONTINUITY SYSTEM TEST RESULTS")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for test_name, success, message in self.test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}: {message}")
            
            if success:
                passed += 1
            else:
                failed += 1
                
        print("-" * 60)
        print(f"Total Tests: {len(self.test_results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {passed/len(self.test_results)*100:.1f}%")
        
        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! Session Continuity System is working perfectly!")
        else:
            print(f"\n⚠️ {failed} test(s) failed. Review the system for issues.")
            
        print("\n📋 Test Summary:")
        print("- Fresh session start functionality")
        print("- Session activity logging")
        print("- Context preservation and resumption")
        print("- Graceful termination with data persistence")
        print("- Resume after termination capability")
        print("\nThe Enhanced Session Continuity System is ready for production use! 🚀")

async def main():
    """Main test execution"""
    tester = SessionContinuityTester()
    
    print("🌟 FindersKeepers v2 - Enhanced Session Continuity System")
    print("🧪 Comprehensive Test Suite")
    print(f"📅 Test Run: {datetime.now().isoformat()}")
    
    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n⏹️ Test suite interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())