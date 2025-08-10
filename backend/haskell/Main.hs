{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE ScopedTypeVariables #-}

module Main where

import Web.Scotty as S
import Data.Aeson (FromJSON, ToJSON, encode, decode)
import GHC.Generics
import qualified Data.Text.Lazy as TL
import qualified Data.Text as T
import qualified Data.ByteString.Char8 as BS
import Data.IORef
import qualified Data.Map as Map
import Control.Monad.IO.Class (liftIO)
import Network.HTTP.Types.Status
import Network.Wai.Middleware.Cors
import Language.Haskell.Interpreter
import Control.Exception (try, SomeException)
import Data.Maybe (fromMaybe)
import System.Environment (lookupEnv)

data ExecuteRequest = ExecuteRequest
  { code :: T.Text
  } deriving (Generic, Show)

instance FromJSON ExecuteRequest
instance ToJSON ExecuteRequest

data ExecuteResponse = ExecuteResponse
  { output :: T.Text
  , error :: Maybe T.Text
  } deriving (Generic, Show)

instance FromJSON ExecuteResponse
instance ToJSON ExecuteResponse

data HealthResponse = HealthResponse
  { status :: T.Text
  } deriving (Generic, Show)

instance ToJSON HealthResponse

data ResetResponse = ResetResponse
  { message :: T.Text
  } deriving (Generic, Show)

instance ToJSON ResetResponse

type SessionId = String
type SessionState = Map.Map SessionId [String]

executeHaskell :: String -> IO (Either String String)
executeHaskell code = do
  result <- try $ runInterpreter $ do
    setImports ["Prelude"]
    eval code
  case result of
    Left (e :: SomeException) -> return $ Left (show e)
    Right (Left e) -> return $ Left (errorString e)
    Right (Right r) -> return $ Right r

errorString :: InterpreterError -> String
errorString (UnknownError s) = "Unknown error: " ++ s
errorString (WontCompile es) = unlines $ map errMsg es
errorString (NotAllowed s) = "Not allowed: " ++ s
errorString (GhcException s) = "GHC exception: " ++ s

main :: IO ()
main = do
  env <- lookupEnv "ENVIRONMENT"
  backendPortStr <- lookupEnv "BACKEND_PORT"
  corsOriginsEnv <- lookupEnv "CORS_ORIGINS"
  
  let environment = fromMaybe "development" env
  let backendPort = maybe 8000 read backendPortStr
  let corsOrigins = fromMaybe "http://localhost:8080" corsOriginsEnv
  
  let isDev = environment == "development"
  let corsPolicy = if isDev
        then simpleCorsResourcePolicy
          { corsOrigins = Nothing
          , corsMethods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
          , corsRequestHeaders = ["Content-Type"]
          }
        else simpleCorsResourcePolicy
          { corsOrigins = Just ([BS.pack corsOrigins], True)
          , corsMethods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
          , corsRequestHeaders = ["Content-Type"]
          }
  
  sessionsRef <- newIORef Map.empty
  
  scotty backendPort $ do
    middleware $ cors (const $ Just corsPolicy)
    
    S.get "/health" $ do
      json $ HealthResponse "healthy"
    
    S.post "/execute/:sessionId" $ do
      sessionId <- param "sessionId" :: ActionM String
      req <- jsonData :: ActionM ExecuteRequest
      let codeStr = T.unpack (code req)
      
      if null codeStr
        then do
          S.status status400
          json $ ExecuteResponse "" (Just "Code cannot be empty")
        else do
          result <- liftIO $ executeHaskell codeStr
          case result of
            Left err -> json $ ExecuteResponse "" (Just $ T.pack err)
            Right out -> json $ ExecuteResponse (T.pack out) Nothing
    
    S.post "/reset/:sessionId" $ do
      sessionId <- param "sessionId" :: ActionM String
      sessions <- liftIO $ readIORef sessionsRef
      liftIO $ writeIORef sessionsRef $ Map.delete sessionId sessions
      json $ ResetResponse "Session reset successfully"
    
    S.options (regex ".*") $ do
      addHeader "Access-Control-Allow-Origin" "*"
      addHeader "Access-Control-Allow-Methods" "GET, POST, PUT, DELETE, OPTIONS"
      addHeader "Access-Control-Allow-Headers" "Content-Type"
      S.status status200