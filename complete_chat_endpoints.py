        # Generate response using Ollama
        assistant_response = await generate_ollama_response(full_prompt, request.model)
        
        # Add assistant message to conversation
        assistant_message = ChatMessage(role="assistant", content=assistant_response)
        conversations[conversation_id].append(assistant_message)
        
        # Calculate response time
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return ChatResponse(
            message=assistant_response,
            conversation_id=conversation_id,
            sources=context_sources,
            model_used=request.model,
            response_time_ms=response_time,
            tokens_used=len(assistant_response.split())  # Rough token estimate
        )
        
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")